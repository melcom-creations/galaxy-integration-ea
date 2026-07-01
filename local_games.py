import glob
import re
import functools
import logging
import os
import platform
import urllib.parse

if platform.system() == "Windows":
    from ctypes import byref, sizeof, windll, create_unicode_buffer, FormatError, WinError
    from ctypes.wintypes import DWORD

    from typing import Optional, Set, List
else:
    import psutil

from dataclasses import dataclass
from enum import Enum, auto, Flag
from typing import Iterator, Tuple

from galaxy.api.errors import FailedParsingManifest
from galaxy.api.types import LocalGame, LocalGameState


logger = logging.getLogger(__name__)


class _State(Enum):
    kInvalid = auto()
    kError = auto()
    kPaused = auto()
    kPausing = auto()
    kCanceling = auto()
    kReadyToStart = auto()
    kInitializing = auto()
    kResuming = auto()
    kPreTransfer = auto()
    kPendingInstallInfo = auto()
    kPendingEulaLangSelection = auto()
    kPendingEula = auto()
    kEnqueued = auto()
    kTransferring = auto()
    kPendingDiscChange = auto()
    kPostTransfer = auto()
    kMounting = auto()
    kUnmounting = auto()
    kUnpacking = auto()
    kDecrypting = auto()
    kReadyToInstall = auto()
    kPreInstall = auto()
    kInstalling = auto()  # This status is used for games which are installing or updating
    kPostInstall = auto()
    kFetchLicense = auto()
    kCompleted = auto()

    @classmethod
    def _missing_(cls, value):
        logging.warning('Unrecognized state: %s' % value)
        return cls.kInvalid


@dataclass
class _Manifest:
    game_id: str
    state: _State
    prev_state: _State
    ddinstallalreadycompleted: str
    dipinstallpath: str
    ddinitialdownload: str


class OriginGameState(Flag):
    None_ = 0
    Installed = 1
    Playable = 2


def _parse_msft_file(filepath):
    with open(filepath, encoding="utf-8") as file:
        data = file.read()
    parsed_url = urllib.parse.urlparse(data)
    parsed_data = dict(urllib.parse.parse_qsl(parsed_url.query))
    try:
        game_id = parsed_data["id"]
    except KeyError as e:
        raise FailedParsingManifest({"file": filepath, "exception": e, "parsed_data": parsed_data})
    state = _State[parsed_data.get("currentstate", "<missing currentstate>")]
    prev_state = _State[parsed_data.get("previousstate", "<missing previousstate>")]
    ddinstallalreadycompleted = parsed_data.get("ddinstallalreadycompleted", "0")
    dipinstallpath = parsed_data.get("dipinstallpath", "")
    ddinitialdownload = parsed_data.get("ddinitialdownload", "0")

    return _Manifest(game_id, state, prev_state, ddinstallalreadycompleted, dipinstallpath, ddinitialdownload)


def get_local_games_manifests(manifests_stats):
    manifests = []
    for filename in manifests_stats.keys():
        try:
            parsed_mfst_file = _parse_msft_file(filename)
        except FailedParsingManifest as e:
            logging.warning("Failed to parse file %s: %s", filename, e.data)
        except Exception as e:
            logging.exception(repr(e))
        else:
            manifests.append(parsed_mfst_file)
    return manifests


def parse_map_crc_for_total_size(filepath) -> int:
    with open(filepath, 'r', encoding='utf-16-le') as f:
        content = f.read()
    pattern = r'size=(\d+)'
    sizes = re.findall(pattern, content)
    return functools.reduce(lambda a, b : a + int(b), sizes, 0)


if platform.system() == "Windows":
    def get_process_info(pid) -> Tuple[int, Optional[str]]:
        _MAX_PATH = 260
        _PROC_QUERY_LIMITED_INFORMATION = 0x1000
        _WIN32_PATH_FORMAT = 0x0000

        h_process = windll.kernel32.OpenProcess(_PROC_QUERY_LIMITED_INFORMATION, False, pid)
        if not h_process:
            return pid, None

        def get_process_file_name() -> Optional[str]:
            try:
                file_name_buffer = create_unicode_buffer(_MAX_PATH)
                file_name_len = DWORD(len(file_name_buffer))

                return file_name_buffer[:file_name_len.value] if windll.kernel32.QueryFullProcessImageNameW(
                    h_process, _WIN32_PATH_FORMAT, file_name_buffer, byref(file_name_len)
                ) else None

            finally:
                windll.kernel32.CloseHandle(h_process)

        return pid, get_process_file_name()


    def get_process_ids() -> Set[int]:
        _PROC_ID_T = DWORD
        list_size = 4096

        def try_get_info_list(list_size) -> Tuple[int, List[int]]:
            result_size = DWORD()
            proc_id_list = (_PROC_ID_T * list_size)()

            if not windll.psapi.EnumProcesses(byref(proc_id_list), sizeof(proc_id_list), byref(result_size)):
                raise WinError(descr="Failed to get process ID list: %s" % FormatError())

            size = int(result_size.value / sizeof(_PROC_ID_T()))
            return proc_id_list[:size]

        while True:
            proc_id_list = try_get_info_list(list_size)
            if len(proc_id_list) < list_size:
                return proc_id_list
            # If the returned collection is not smaller than the requested size, some PIDs may have been missed.
            list_size *= 2

        return set(proc_id_list)


    def process_iter() -> Iterator[Tuple[int, str]]:
        try:
            for pid in get_process_ids():
                yield get_process_info(pid)
        except OSError:
            logger.exception("Failed to iterate over the process list")
            pass

else:
    def process_iter() -> Iterator[Tuple[int, str]]:
        for pid in psutil.pids():
            try:
                yield pid, psutil.Process(pid=pid).as_dict(attrs=["exe"])["exe"]
            except psutil.NoSuchProcess:
                pass
            except StopIteration:
                raise
            except Exception:
                logger.exception("Failed to get information for PID=%s" % pid)


def read_state(manifest : _Manifest) -> OriginGameState:
    game_state = OriginGameState.None_
    if manifest.state == _State.kReadyToStart and manifest.prev_state == _State.kCompleted:
        game_state |= OriginGameState.Installed
        game_state |= OriginGameState.Playable
    if manifest.ddinstallalreadycompleted == "1" and manifest.state != _State.kPostInstall:
        game_state |= OriginGameState.Playable
    if manifest.state in (_State.kInstalling, _State.kInitializing, _State.kTransferring, _State.kEnqueued, _State.kPostInstall) and manifest.ddinitialdownload == "0":
        game_state |= OriginGameState.Installed
    return game_state


def get_local_games_from_manifests(manifests):
    local_games = []

    running_processes = [exe for pid, exe in process_iter() if exe is not None]

    def is_game_running(game_folder_name):
        for exe in running_processes:
            if game_folder_name in exe:
                return True
        return False

    for manifest in manifests:

        state = LocalGameState.None_

        game_state = read_state(manifest)
        if OriginGameState.Installed in game_state \
                or OriginGameState.Playable in game_state:
            state |= LocalGameState.Installed

        if manifest.dipinstallpath and is_game_running(manifest.dipinstallpath):
            state |= LocalGameState.Running

        local_games.append(LocalGame(manifest.game_id, state))

    return local_games


def get_local_games_manifest_stats(path):
    path = os.path.abspath(path)
    return {
        filename: os.stat(filename)
        for filename in glob.glob(
            os.path.join(path, "**", "*.mfst"),
            recursive=True
        )
    }


def get_state_changes(old_list, new_list):
    old_dict = {x.game_id: x.local_game_state for x in old_list}
    new_dict = {x.game_id: x.local_game_state for x in new_list}
    result = []
    # Games that disappeared since the last scan.
    result.extend(LocalGame(game_id, LocalGameState.None_) for game_id in old_dict.keys() - new_dict.keys())
    # Games that appeared since the last scan.
    result.extend(local_game for local_game in new_list if local_game.game_id in new_dict.keys() - old_dict.keys())
    # Games whose local state differs from the previous scan.
    result.extend(
        LocalGame(game_id, new_dict[game_id])
        for game_id in new_dict.keys() & old_dict.keys()
        if new_dict[game_id] != old_dict[game_id]
    )
    return result


def get_local_content_path():
    platform_id = platform.system()

    if platform_id == "Windows":
        local_content_path = os.path.join(os.environ.get("ProgramData", os.environ.get("SystemDrive", "C:") + R"\ProgramData"), "Origin", "LocalContent")
    elif platform_id == "Darwin":
        local_content_path = os.path.join(os.sep, "Library", "Application Support", "Origin", "LocalContent")
    else:
        local_content_path = "."  # Fallback path for platforms without Origin local content directories.

    return local_content_path


class LocalGames:

    def __init__(self, path):
        self._path = path
        self._manifests_stats = get_local_games_manifest_stats(self._path)
        try:
            self._manifests = get_local_games_manifests(self._manifests_stats)
        except FailedParsingManifest as e:
            self._manifests = []
            self._local_games = []
            logger.warning("Failed to parse local games on start: {}, {}".format(e.message, e.data))
            return

        self._local_games = get_local_games_from_manifests(self._manifests)

    @property
    def local_games(self):
        return self._local_games

    def update(self):
        '''
        returns list of changed games (added, removed, or changed)
        updated local_games property
        '''
        new_manifests_stats = get_local_games_manifest_stats(self._path)
        if new_manifests_stats != self._manifests_stats:
            self._manifests_stats = new_manifests_stats
            self._manifests = get_local_games_manifests(self._manifests_stats)

        new_local_games = get_local_games_from_manifests(self._manifests)
        notify_list = get_state_changes(self._local_games, new_local_games)
        self._local_games = new_local_games

        return self._local_games, notify_list
