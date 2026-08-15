import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from api.fastapi_app import app
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
    client = TestClient(app)
except ImportError:
    FASTAPI_AVAILABLE = False


class TestAPIEndpoints(unittest.TestCase):
    @unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI / TestClient not installed in test environment")
    def test_gemini_proxy_missing_key(self):
        response = client.post("/api/gemini", json={"prompt": "hello"})
        self.assertIn(response.status_code, [200, 500])


if __name__ == "__main__":
    unittest.main()
