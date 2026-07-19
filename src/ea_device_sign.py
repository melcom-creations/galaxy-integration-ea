# ea_device_sign.py
# Generates the EA Desktop device token used during authentication.
# Collects hardware identifiers, builds a signed payload and returns
# the pc_sign value expected by the EA service layer.
#
# Inspired by pcsign_hash.py from BellezaEmporium's galaxy-integration-ead.
# BellezaEmporium credits @imLinguin & ArmchairDevelopers for the hardware info approach.

import base64
import ctypes
import datetime
import hashlib
import hmac
import json
import logging
import platform
import random
import re
import struct
import subprocess
import threading
import time
from importlib import import_module
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Final

logger = logging.getLogger(__name__)


def fnv1a_hash(data: bytes) -> int:
    value = 0xcbf29ce484222325
    prime = 0x100000001b3
    for byte in data:
        value = ((value ^ byte) * prime) & 0xFFFFFFFFFFFFFFFF
    return value


_cpuinfo_lib: Any = None

try:
    _cpuinfo_lib = import_module("cpuinfo")
    _CPUINFO_AVAILABLE = True
except ImportError:
    _CPUINFO_AVAILABLE = False

    _IS_64BIT: Final = struct.calcsize("P") == 8

    # Machine code that invokes CPUID and writes eax/ebx/ecx/edx into the supplied buffer.
    # Hex notation keeps the definition compact, and fromhex() ignores embedded whitespace.
    _CPUID_SHELLCODE_64: Final = bytes.fromhex(
        "5357 89C8 4889D7 31C9 0FA2"  # push rbx/rdi; mov eax←leaf; save buf ptr; cpuid
        " 8907 895F04 894F08 89570C"  # write eax/ebx/ecx/edx into buffer
        " 5F5BC3"                     # pop rdi/rbx; ret
    )
    _CPUID_SHELLCODE_32: Final = bytes.fromhex(
        "5357 8B44240C 31C9 0FA2"     # push ebx/edi; mov eax←[esp+C]; cpuid
        " 8B7C2410"                   # mov edi←[esp+10] (buf ptr)
        " 8907 895F04 894F08 89570C"  # write eax/ebx/ecx/edx into buffer
        " 5F5BC3"                     # pop edi/ebx; ret
    )

    def _run_cpuid(leaf: int) -> tuple[int, int, int, int]:
        if platform.system() != "Windows":
            return 0, 0, 0, 0
        k32 = ctypes.windll.kernel32
        k32.VirtualAlloc.restype = ctypes.c_void_p
        k32.VirtualAlloc.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32
        ]
        k32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]

        code = _CPUID_SHELLCODE_64 if _IS_64BIT else _CPUID_SHELLCODE_32
        addr = k32.VirtualAlloc(None, len(code), 0x3000, 0x40)
        if not addr:
            raise OSError("VirtualAlloc failed")
        try:
            ctypes.memmove(addr, code, len(code))
            regs = (ctypes.c_uint32 * 4)()
            fn = ctypes.CFUNCTYPE(None, ctypes.c_uint32,
                                  ctypes.POINTER(ctypes.c_uint32 * 4))(addr)
            fn(leaf, regs)
            return tuple(regs)  # type: ignore[return-value]
        finally:
            k32.VirtualFree(addr, 0, 0x8000)


@dataclass(frozen=True, slots=True)
class CpuInfo:
    eax: int = 0
    ebx: int = 0
    ecx: int = 0
    edx: int = 0
    manufacturer: str = ""
    brand_name: str = ""

    @classmethod
    def collect(cls) -> "CpuInfo":
        eax = ebx = ecx = edx = 0
        manufacturer = ""
        brand_name = ""

        if platform.system() == "Windows":
            try:
                _, m_ebx, m_edx, m_ecx = _run_cpuid(0)
                f_eax, _, f_ecx, f_edx = _run_cpuid(1)
                eax, ecx, edx = f_eax, f_ecx, f_edx

                vendor_raw = bytearray()
                for reg in (m_ebx, m_edx, m_ecx):
                    vendor_raw += reg.to_bytes(4, "little")
                manufacturer = vendor_raw.decode("ascii", errors="replace")

                brand_raw = bytearray()
                done = False
                for leaf in (0x80000002, 0x80000003, 0x80000004):
                    if done:
                        break
                    for reg in _run_cpuid(leaf):
                        for byte in reg.to_bytes(4, "little"):
                            if byte == 0:
                                done = True
                                break
                            brand_raw.append(byte)
                        if done:
                            break
                brand_raw += b"\x00" * max(0, 47 - len(brand_raw))
                brand_name = brand_raw.rstrip(b"\x00").decode("ascii", errors="replace")
            except Exception as exc:
                logger.warning("CPUID call failed: %s", exc)

        if _CPUINFO_AVAILABLE and (not manufacturer or not brand_name):
            try:
                info = _cpuinfo_lib.get_cpu_info()
                manufacturer = manufacturer or info.get("vendor_id_raw", "")
                brand_name   = brand_name   or info.get("brand_raw", "")
            except Exception as exc:
                logger.debug("py-cpuinfo fallback failed: %s", exc)

        return cls(eax=eax, ebx=ebx, ecx=ecx, edx=edx,
                   manufacturer=manufacturer, brand_name=brand_name)


def _read_mac_address() -> str | None:
    """Return MAC formatted as '$<hex>', or None if locally-administered."""
    try:
        import uuid
        node = uuid.getnode()
        if (node >> 40) & 1:
            return None
        return f"${node:012x}"
    except Exception:
        return None


def _pci_pnp_id(version: int, vendor: int | None, device: int | None, revision: int | None) -> str:
    sections = [
        f"VEN_{vendor or 0:04X}",
        f"DEV_{device or 0:04X}",
        f"SUBSYS_{0:08X}",
    ]
    if version < 4:
        sections.append(f"REV_{revision or 0:02X}")
    else:
        sections += [
            f"REV_{revision or 0:02X}\\0",
            f"{0xDEADBEEF:08X}",
            "0",
            f"{0xDEAD:04X}",
        ]
    return "PCI\\" + "&".join(sections)


@dataclass(slots=True)
class DeviceInfo:
    version: int
    board_manufacturer: str = ""
    board_sn: str = ""
    bios_manufacturer: str = ""
    bios_sn: str = ""
    os_install_date: str = ""
    os_sn: str = ""
    disk_sn: str = ""
    volume_sn: str = ""
    gpu_pnp_id: str | None = None
    mac: str | None = None
    cpu: CpuInfo = field(default_factory=CpuInfo)
    hostname: str = ""

    @classmethod
    def build(cls, version: int) -> "DeviceInfo":
        system = platform.system()
        try:
            if system == "Windows":
                return cls._from_windows(version)
            if system == "Darwin":
                return cls._from_macos(version)
            logger.error("Unsupported platform: %s", system)
        except Exception as exc:
            logger.warning("DeviceInfo.build failed (%s): %s", system, exc)
        return cls(version=version)

    @classmethod
    def _from_windows(cls, version: int) -> "DeviceInfo":
        ps_script = Path(__file__).parent / "pc_sign_ps.ps1"
        raw: dict[str, Any] = {}

        if ps_script.exists():
            try:
                proc = subprocess.run(
                    [
                        "powershell", "-NoProfile", "-NonInteractive",
                        "-ExecutionPolicy", "Bypass",
                        "-File", str(ps_script),
                    ],
                    capture_output=True, timeout=15,
                    text=True, encoding="utf-8", errors="ignore",
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    parsed = json.loads(proc.stdout.strip())
                    raw = parsed[0] if isinstance(parsed, list) else parsed
            except Exception as exc:
                logger.warning("PowerShell script error: %s", exc)

        if not raw:
            raw = cls._wmic_fallback()

        gpu_pnp = cls._resolve_gpu_pnp(raw, version)

        return cls(
            version=version,
            board_manufacturer=raw.get("mbm") or raw.get("board_manufacturer", "Microsoft Corporation"),
            board_sn=raw.get("msn") or raw.get("board_sn", "None"),
            bios_manufacturer=raw.get("bbm") or raw.get("bios_manufacturer", "Microsoft Corporation"),
            bios_sn=raw.get("bsn") or raw.get("bios_sn", "None"),
            os_install_date=raw.get("osi", "1970-01-0100:00:00.000000000+0000"),
            os_sn=raw.get("osn") or raw.get("os_sn", "None"),
            disk_sn=raw.get("hsn") or raw.get("disk_sn", "None"),
            volume_sn=raw.get("volume_sn") or cls._volume_serial(),
            gpu_pnp_id=gpu_pnp,
            mac=raw.get("mac") or _read_mac_address(),
            cpu=CpuInfo.collect(),
            hostname=platform.node(),
        )

    @classmethod
    def _from_macos(cls, version: int) -> "DeviceInfo":
        def run(*args: str, timeout: int = 10) -> str:
            try:
                r = subprocess.run(
                    list(args), capture_output=True, text=True,
                    timeout=timeout, encoding="utf-8", errors="ignore",
                )
                return r.stdout if r.returncode == 0 else ""
            except Exception:
                return ""

        def ioreg_value(key: str, text: str) -> str:
            if m := re.search(rf'"{key}"\s*=\s*"([^"]+)"', text):
                return m.group(1)
            return ""

        ioreg_out = run("ioreg", "-d2", "-c", "IOPlatformExpertDevice")
        board_sn = ioreg_value("IOPlatformSerialNumber", ioreg_out) or "None"
        os_sn    = ioreg_value("IOPlatformUUID",         ioreg_out) or "None"

        disk_sn = "None"
        for line in run("diskutil", "info", "/").splitlines():
            if "Volume UUID:" in line:
                parts = line.split()
                if len(parts) >= 3:
                    disk_sn = parts[2]
                break

        gpu_pnp = None
        sp_json = run("system_profiler", "SPDisplaysDataType", "-json")
        if sp_json:
            try:
                items = json.loads(sp_json).get("SPDisplaysDataType", [])
                if items:
                    gpu_entry = items[0]
                    dev_id  = int(gpu_entry.get("spdisplays_device-id",   "0x0000"), 16)
                    rev_id  = int(gpu_entry.get("spdisplays_revision-id", "0x00"),   16)
                    gpu_pnp = _pci_pnp_id(version, None, dev_id, rev_id)
            except Exception as exc:
                logger.debug("system_profiler GPU parse error: %s", exc)

        return cls(
            version=version,
            board_manufacturer="Apple Inc.",
            board_sn=board_sn,
            bios_manufacturer="Apple Inc.",
            bios_sn=board_sn,
            os_install_date="1970010100:00:00.000000000+0000",
            os_sn=os_sn,
            disk_sn=disk_sn,
            volume_sn="43000000",
            gpu_pnp_id=gpu_pnp,
            mac=_read_mac_address(),
            cpu=CpuInfo.collect(),
            hostname=platform.node(),
        )

    def gpu_device_id(self) -> int:
        if self.gpu_pnp_id and (m := re.search(r"DEV_([0-9A-Fa-f]+)", self.gpu_pnp_id)):
            try:
                return int(m.group(1), 16)
            except ValueError:
                pass
        return 0

    def machine_id(self) -> str:
        parts = [
            self.board_manufacturer,
            self.board_sn,
            self.bios_manufacturer,
            self.bios_sn,
            self.os_install_date,
            self.os_sn,
        ]
        if self.mac:
            parts.append(self.mac)
        return str(fnv1a_hash("".join(parts).encode("utf-8")))

    def hardware_hash(self) -> str:
        cpu = self.cpu
        cpu_edx      = f"{cpu.edx:08x}"
        cpu_edx_eax  = f"{cpu.edx:08X}{cpu.eax:08X}"
        cpu_ecx      = f"{cpu.ecx:08x}"
        gpu          = self.gpu_pnp_id or "None"

        parts = [self.board_manufacturer, self.board_sn]

        if self.version in (0, 1):
            parts += [self.hostname, self.bios_manufacturer, self.bios_sn,
                      self.os_install_date, self.os_sn]
        elif self.version == 2:
            parts += [self.bios_manufacturer, self.bios_sn,
                      self.os_install_date, self.os_sn,
                      self.volume_sn, gpu, cpu.manufacturer, cpu_edx, cpu_ecx]
        elif self.version == 3:
            parts += [self.bios_manufacturer, self.bios_sn,
                      self.volume_sn, gpu, cpu.manufacturer, cpu_edx, cpu_ecx]
        else:
            parts += [self.bios_manufacturer, self.bios_sn,
                      self.volume_sn, gpu, cpu.manufacturer, cpu_edx_eax]

        combined = ";".join(parts) + ";"
        if self.version >= 2:
            combined += cpu.brand_name + ";"

        logger.debug('Hardware hash input: "%s"', combined)
        digest = hashlib.sha1(combined.encode("utf-8")).digest()
        return digest.hex() if self.version >= 4 else "".join(f"{b:x}" for b in digest)

    @staticmethod
    def _resolve_gpu_pnp(raw: dict[str, Any], version: int) -> str | None:
        gid_raw = raw.get("gid", 0)
        try:
            dev_id = (
                int(gid_raw, 16)
                if isinstance(gid_raw, str) and gid_raw.startswith(("0x", "0X"))
                else int(gid_raw or 0)
            )
        except (ValueError, TypeError):
            dev_id = 0
        return _pci_pnp_id(version, None, dev_id, None) if dev_id else raw.get("gpu_pnp_id")

    @staticmethod
    def _wmic_fallback() -> dict[str, Any]:
        """Collect hardware identifiers via PowerShell CIM when pc_sign_ps.ps1 is absent."""
        ps_cmd = (
            "$b  = Get-CimInstance -ClassName Win32_BaseBoard;"
            "$bi = Get-CimInstance -ClassName Win32_BIOS;"
            "$os = Get-CimInstance -ClassName Win32_OperatingSystem;"
            "$hd = Get-CimInstance -ClassName Win32_DiskDrive |"
            " Sort-Object Index | Select-Object -First 1;"
            "[ordered]@{"
            " mbm=$b.Manufacturer; msn=$b.SerialNumber;"
            " bbm=$bi.Manufacturer; bsn=$bi.SerialNumber;"
            " osn=$os.SerialNumber;"
            " osi=$os.InstallDate.ToUniversalTime().ToString('yyyyMMddHHmmss.ffffff+000');"
            " hsn=$hd.SerialNumber"
            "} | ConvertTo-Json -Compress"
        )
        try:
            proc = subprocess.run(
                [
                    "powershell", "-NoProfile", "-NonInteractive",
                    "-ExecutionPolicy", "Bypass",
                    "-Command", ps_cmd,
                ],
                capture_output=True, timeout=15,
                text=True, encoding="utf-8", errors="ignore",
            )
            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout.strip())
                return {k: (v or "") for k, v in data.items()}
        except Exception as exc:
            logger.warning("CIM hardware query failed: %s", exc)
        return {}

    @staticmethod
    def _volume_serial() -> str:
        try:
            serial = ctypes.c_uint32(0)
            ctypes.windll.kernel32.GetVolumeInformationW(
                "C:\\", None, 0, ctypes.byref(serial), None, None, None, 0,
            )
            return f"{serial.value:08x}"
        except Exception:
            return "00000000"


class DeviceInfoCache:
    _instance: "DeviceInfoCache | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "DeviceInfoCache":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_ready"):
            self._info:           DeviceInfo | None = None
            self._fetched_at:     float | None      = None
            self._ttl:            int               = 3600
            self._ready = True

    def get(self, version: int) -> DeviceInfo:
        now = time.monotonic()
        if (self._info is not None
                and self._fetched_at is not None
                and now - self._fetched_at < self._ttl):
            return self._info
        with self._lock:
            if (self._info is not None
                    and self._fetched_at is not None
                    and now - self._fetched_at < self._ttl):
                return self._info
            self._info = DeviceInfo.build(version)
            self._fetched_at = now
            return self._info

    def invalidate(self) -> None:
        with self._lock:
            self._info = None
            self._fetched_at = None


class SignMethod(Enum):
    V1 = "v1"
    V2 = "v2"


_HMAC_KEYS: Final[dict[SignMethod, bytes]] = {
    SignMethod.V1: b"ISa3dpGOc8wW7Adn4auACSQmaccrOyR2",
    SignMethod.V2: b"nt5FfJbdPzNcl2pkC3zgjO43Knvscxft",
}


@dataclass(slots=True)
class DeviceToken:
    hw_version: int       = 4
    av:         str       = "v1"
    method:     SignMethod = field(
        default_factory=lambda: random.choice(list(SignMethod))
    )

    board_manufacturer: str        = field(init=False)
    board_sn:           str        = field(init=False)
    bios_manufacturer:  str        = field(init=False)
    bios_sn:            str        = field(init=False)
    os_install_date:    str        = field(init=False)
    os_sn:              str        = field(init=False)
    disk_sn:            str        = field(init=False)
    volume_sn:          str        = field(init=False)
    gpu_pnp_id:         str | None = field(init=False)
    gid:                int        = field(init=False)
    mac:                str | None = field(init=False)
    mid:                str        = field(init=False)
    hostname:           str        = field(init=False)
    ts:                 str        = field(init=False)

    def __post_init__(self):
        info = DeviceInfoCache().get(self.hw_version)
        self.board_manufacturer = info.board_manufacturer
        self.board_sn           = info.board_sn
        self.bios_manufacturer  = info.bios_manufacturer
        self.bios_sn            = info.bios_sn
        self.os_install_date    = info.os_install_date
        self.os_sn              = info.os_sn
        self.disk_sn            = info.disk_sn
        self.volume_sn          = info.volume_sn
        self.gpu_pnp_id         = info.gpu_pnp_id
        self.gid                = info.gpu_device_id()
        self.mac                = info.mac
        self.mid                = info.machine_id()
        self.hostname           = info.hostname
        self.ts                 = self._timestamp()

    @staticmethod
    def _timestamp() -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        ms  = now.microsecond // 1000
        return (
            f"{now.year}-{now.month:02d}-{now.day:02d} "
            f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}:{ms:03d}"
        )

    def _sign_key(self) -> bytes:
        return _HMAC_KEYS[self.method]

    def _as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "av":  self.av,
            "bsn": self.bios_sn,
            "gid": self.gid,
            "hsn": self.disk_sn,
            "mid": self.mid,
            "msn": self.board_sn,
            "sv":  self.method.value,
            "ts":  self.ts,
        }
        if self.mac is not None:
            payload["mac"] = self.mac
        return payload

    @staticmethod
    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    def sign(self) -> str:
        body = self._b64url(json.dumps(self._as_dict(), separators=(",", ":")).encode())
        sig  = hmac.new(self._sign_key(), body.encode("ascii"), hashlib.sha256).digest()
        return f"{body}.{self._b64url(sig)}"

    @classmethod
    def generate(cls, method: SignMethod, hw_version: int = 4) -> str:
        return cls(hw_version=hw_version, method=method).sign()

    @staticmethod
    def warm_cache(hw_version: int = 4) -> None:
        try:
            DeviceInfoCache().get(hw_version)
        except Exception:
            pass


def decode_jwt_user(token: str) -> tuple[str, str, str]:
    try:
        _, payload, _ = token.split(".")
        rem = len(payload) % 4
        if rem:
            payload += "=" * (4 - rem)
        nexus = json.loads(base64.urlsafe_b64decode(payload))["nexus"]
        return (
            nexus.get("pid",  ""),
            nexus.get("psid", ""),
            nexus.get("psif", [{}])[0].get("dis", ""),
        )
    except Exception as exc:
        logger.error("JWT decode failed: %s", exc)
        return "", "", ""


def build_device_token(
    method: SignMethod | None = None,
    hw_version: int = 4,
) -> str:
    if method is None:
        method = random.choice(list(SignMethod))
    return DeviceToken.generate(method, hw_version=hw_version)


def prime_device_cache(hw_version: int = 4) -> None:
    DeviceToken.warm_cache(hw_version)
