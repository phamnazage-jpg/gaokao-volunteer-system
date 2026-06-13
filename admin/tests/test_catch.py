"""T9.4 @catch 装饰器测试."""

from __future__ import annotations

import asyncio
import io
import json

import pytest

from admin.errors import BusinessError, DATA_PERSIST_FAILED, SYS_INTERNAL_ERROR
from admin.logging_utils import configure_logging, reset_logging_for_tests


class TestCatchDecorator:
    def test_maps_sync_exception_to_business_error_and_logs(self):
        stream = io.StringIO()
        reset_logging_for_tests()
        configure_logging(level="INFO", fmt="json", stream=stream)

        from admin.errors import catch

        @catch(DATA_PERSIST_FAILED)
        def _boom() -> None:
            raise ValueError("db unavailable")

        with pytest.raises(BusinessError) as cm:
            _boom()

        assert cm.value.code == DATA_PERSIST_FAILED
        assert isinstance(cm.value.__cause__, ValueError)

        payload = json.loads(stream.getvalue().strip())
        assert payload["level"] == "error"
        assert payload["ctx"]["event"] == "caught_exception"
        assert payload["ctx"]["code"] == str(DATA_PERSIST_FAILED)
        assert payload["ctx"]["function"] == "_boom"
        assert payload["exc"]["type"] == "ValueError"

    def test_passthrough_existing_business_error(self):
        from admin.errors import catch

        @catch(DATA_PERSIST_FAILED)
        def _boom() -> None:
            raise BusinessError(SYS_INTERNAL_ERROR)

        with pytest.raises(BusinessError) as cm:
            _boom()

        assert cm.value.code == SYS_INTERNAL_ERROR
        assert cm.value.__cause__ is None

    def test_supports_async_function(self):
        from admin.errors import catch

        @catch(DATA_PERSIST_FAILED)
        async def _boom() -> None:
            raise RuntimeError("async boom")

        with pytest.raises(BusinessError) as cm:
            asyncio.run(_boom())

        assert cm.value.code == DATA_PERSIST_FAILED
        assert isinstance(cm.value.__cause__, RuntimeError)

    def test_reraise_true_preserves_original_exception(self):
        from admin.errors import catch

        @catch(DATA_PERSIST_FAILED, reraise=True)
        def _boom() -> None:
            raise RuntimeError("keep original")

        with pytest.raises(RuntimeError, match="keep original"):
            _boom()
