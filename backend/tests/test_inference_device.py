def test_resolve_inference_device_prefers_cuda_when_available(monkeypatch):
    import inference_device

    monkeypatch.delenv("SAFEVISION_INFERENCE_DEVICE", raising=False)
    monkeypatch.setattr(inference_device.torch.cuda, "is_available", lambda: True)

    assert inference_device.resolve_inference_device() == "cuda:0"


def test_resolve_inference_device_honors_cpu_override(monkeypatch):
    import inference_device

    monkeypatch.setenv("SAFEVISION_INFERENCE_DEVICE", "cpu")
    monkeypatch.setattr(inference_device.torch.cuda, "is_available", lambda: True)

    assert inference_device.resolve_inference_device() == "cpu"


def test_ppe_adapter_passes_resolved_device_to_yolo():
    from inference_service import PPEModelAdapter

    class FakeResult:
        boxes = []
        names = {}

    class FakeModel:
        def __init__(self):
            self.kwargs = None

        def __call__(self, frame, **kwargs):
            self.kwargs = kwargs
            return [FakeResult()]

    fake_model = FakeModel()
    adapter = PPEModelAdapter.__new__(PPEModelAdapter)
    adapter.available = True
    adapter.model_key = "vest"
    adapter._model = fake_model
    adapter._person_model = None
    adapter.inference_device = "cuda:0"
    adapter.inference_confidence = 0.35
    adapter.normalized_target_labels = set()
    adapter._absence_uses_features = False
    adapter._absence_uses_person_overlap = False
    adapter._supports_explicit_missing_classes = False
    adapter.supports_qr = False
    adapter.model_classes = []
    adapter.matched_labels = []
    adapter._qr_detector = None

    result = adapter.infer(frame=None, camera_id=4)

    assert result["status"] == "ok"
    assert fake_model.kwargs["device"] == "cuda:0"
