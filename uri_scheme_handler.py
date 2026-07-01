import platform


if platform.system().lower() == "windows":

    import winreg
    import os

    def _get_path_from_cmd_template(cmd_template) -> str:
        return cmd_template.replace("\"", "").partition("%")[0].strip()

    def is_uri_handler_installed(protocol) -> bool:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT, r"{}\shell\open\command".format(protocol)
            ) as key:
                executable_template = winreg.QueryValue(key, None)
                path = _get_path_from_cmd_template(executable_template)
                return os.path.exists(path)
        except OSError:
            return False


elif platform.system().lower() == "darwin":

    from CoreServices.LaunchServices import LSCopyDefaultHandlerForURLScheme
    from AppKit import NSWorkspace

    def is_uri_handler_installed(protocol) -> bool:
        bundle_id = LSCopyDefaultHandlerForURLScheme(protocol)
        if not bundle_id:
            return False
        return (
            NSWorkspace.sharedWorkspace().absolutePathForAppBundleWithIdentifier_(bundle_id)
            is not None
        )


else:

    def is_uri_handler_installed(protocol) -> bool:
        return False
