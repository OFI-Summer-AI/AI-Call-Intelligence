"""
Controls OBS Studio via its built-in WebSocket server (OBS 28+).
Requires: obs-websocket enabled in OBS (Tools > WebSocket Server Settings).
"""

import obsws_python as obs

from app.config import OBS_WS_HOST, OBS_WS_PORT, OBS_WS_PASSWORD


class OBSController:
    def __init__(self):
        self._client = None

    def connect(self):
        self._client = obs.ReqClient(
            host=OBS_WS_HOST,
            port=OBS_WS_PORT,
            password=OBS_WS_PASSWORD or "",
            timeout=10,
        )
        version = self._client.get_version()
        print(f"[OBS] Connected — OBS v{version.obs_version}, "
              f"WebSocket v{version.obs_web_socket_version}")

    def disconnect(self):
        if self._client:
            self._client = None

    def is_recording(self) -> bool:
        status = self._client.get_record_status()
        return status.output_active

    def start_recording(self):
        if not self.is_recording():
            self._client.start_record()
            print("[OBS] Recording started.")
        else:
            print("[OBS] Already recording.")

    def stop_recording(self) -> str | None:
        """Stop recording and return the output file path."""
        if self.is_recording():
            result = self._client.stop_record()
            path = result.output_path
            print(f"[OBS] Recording stopped. File: {path}")
            return path
        else:
            print("[OBS] Not currently recording.")
            return None

    def get_recording_folder(self) -> str:
        profile = self._client.get_profile_parameter(
            parameter_category="SimpleOutput",
            parameter_name="FilePath",
        )
        return profile.parameter_value
