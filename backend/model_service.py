from typing import Callable, Dict, List


class ModelService:
    def __init__(self, conn_factory: Callable, model_definitions: Dict, inference_service):
        self._conn_factory = conn_factory
        self._model_definitions = model_definitions
        self._inference_service = inference_service

    def _ensure_camera_model_rows(self, camera_id: int) -> None:
        with self._conn_factory() as conn:
            for model_key in self._model_definitions.keys():
                conn.execute(
                    """
                    INSERT OR IGNORE INTO camera_models (camera_id, model_key, enabled)
                    VALUES (?, ?, 1)
                    """,
                    (camera_id, model_key),
                )

    def list_global_models(self) -> List[Dict]:
        with self._conn_factory() as conn:
            rows = conn.execute(
                "SELECT model_key, enabled FROM model_settings ORDER BY model_key"
            ).fetchall()
            enabled_map = {row["model_key"]: bool(row["enabled"]) for row in rows}

        items = []
        for model_key, model_info in self._model_definitions.items():
            health = self._inference_service.get_model_health(model_key)
            items.append(
                {
                    "model_key": model_key,
                    "display_name": model_info["display_name"],
                    "description": model_info["description"],
                    "weights_path": model_info["weights_path"],
                    "enabled": enabled_map.get(model_key, True),
                    "available": health["available"],
                    "load_error": health["load_error"],
                    "model_classes": health.get("model_classes", []),
                    "matched_target_labels": health.get("matched_target_labels", []),
                    "configured_target_labels": health.get("configured_target_labels", []),
                }
            )
        return items

    def set_global_enabled(self, model_key: str, enabled: bool) -> bool:
        if model_key not in self._model_definitions:
            return False
        with self._conn_factory() as conn:
            cursor = conn.execute(
                """
                UPDATE model_settings
                SET enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE model_key = ?
                """,
                (int(enabled), model_key),
            )
            return cursor.rowcount > 0

    def list_camera_models(self, camera_id: int) -> List[Dict]:
        self._ensure_camera_model_rows(camera_id)
        with self._conn_factory() as conn:
            rows = conn.execute(
                """
                SELECT
                    cm.model_key,
                    cm.enabled AS camera_enabled,
                    ms.enabled AS global_enabled
                FROM camera_models cm
                JOIN model_settings ms ON ms.model_key = cm.model_key
                WHERE cm.camera_id = ?
                ORDER BY cm.model_key
                """,
                (camera_id,),
            ).fetchall()

        items = []
        for row in rows:
            model_key = row["model_key"]
            health = self._inference_service.get_model_health(model_key)
            items.append(
                {
                    "model_key": model_key,
                    "display_name": self._model_definitions[model_key]["display_name"],
                    "camera_enabled": bool(row["camera_enabled"]),
                    "global_enabled": bool(row["global_enabled"]),
                    "enabled": bool(row["camera_enabled"]) and bool(row["global_enabled"]),
                    "available": health["available"],
                    "load_error": health["load_error"],
                    "model_classes": health.get("model_classes", []),
                    "matched_target_labels": health.get("matched_target_labels", []),
                    "configured_target_labels": health.get("configured_target_labels", []),
                }
            )
        return items

    def set_camera_enabled(self, camera_id: int, model_key: str, enabled: bool) -> bool:
        if model_key not in self._model_definitions:
            return False

        self._ensure_camera_model_rows(camera_id)
        with self._conn_factory() as conn:
            cursor = conn.execute(
                """
                UPDATE camera_models
                SET enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE camera_id = ? AND model_key = ?
                """,
                (int(enabled), camera_id, model_key),
            )
            return cursor.rowcount > 0

    def get_effective_enabled_model_keys(self, camera_id: int) -> List[str]:
        rows = self.list_camera_models(camera_id)
        return [row["model_key"] for row in rows if row["enabled"]]

    def get_global_enabled_model_keys(self) -> List[str]:
        with self._conn_factory() as conn:
            rows = conn.execute(
                "SELECT model_key FROM model_settings WHERE enabled = 1 ORDER BY model_key"
            ).fetchall()
            return [row["model_key"] for row in rows]
