import json
import threading
import time
import unittest
from http.server import HTTPServer
from urllib.request import Request, urlopen

from backend import mcp_shim


class MCPShimTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer((mcp_shim.HOST, mcp_shim.PORT), mcp_shim.MCPHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        # give server a moment to start
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.server.shutdown()
        finally:
            cls.thread.join(timeout=1)

    def post_json(self, path: str, body: dict):
        data = json.dumps(body).encode("utf-8")
        url = f"http://{mcp_shim.HOST}:{mcp_shim.PORT}{path}"
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=5) as resp:
            return json.load(resp), resp.getcode()

    def test_capabilities(self):
        body, status = self.post_json("/mcp/capabilities", {})
        self.assertEqual(status, 200)
        self.assertIn("provider", body)

    def test_generate(self):
        body, status = self.post_json("/mcp/generate", {"prompt": "hello"})
        self.assertEqual(status, 200)
        self.assertIn("output", body)
        self.assertIn("provider", body)


if __name__ == "__main__":
    unittest.main()
