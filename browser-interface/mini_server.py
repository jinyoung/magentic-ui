from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
from playwright.async_api import async_playwright

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "Mini WebSurfer API"})

@app.route('/simple_browse', methods=['POST'])
def simple_browse():
    data = request.get_json()
    url = data.get('url', 'https://example.com')
    
    async def browse():
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect("ws://localhost:37367/default")
        page = await browser.new_page()
        await page.goto(url)
        title = await page.title()
        await browser.close()
        await playwright.stop()
        return {"title": title, "url": url}
    
    result = asyncio.run(browse())
    return jsonify({"success": True, "result": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)
