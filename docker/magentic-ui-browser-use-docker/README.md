# Magentic UI Browser-Use Docker

This Docker container provides a complete browser automation environment with:
- **Browser-Use**: AI-powered browser automation library
- **Playwright**: Web automation framework
- **noVNC**: Web-based VNC client for visual access
- **X11**: Display server for running browsers

## 🚀 Quick Start

### 1. Build and Run
```bash
# Build and start the container
./quick-build.sh

# Or manually:
docker build -t magentic-ui-browser-use .
docker run -d --name magentic-ui-browser-use \
  -p 6080:6080 \
  -p 37367:37367 \
  -p 5001:5001 \
  magentic-ui-browser-use
```

### 2. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| Browser-Use API | http://localhost:5001 | AI browser automation API |
| VNC Web Client | http://localhost:6080 | Visual browser access |
| Playwright WS | ws://localhost:37367/default | Playwright WebSocket |

## 📋 API Endpoints

### Health Check
```bash
curl http://localhost:5001/health
```

### Execute Natural Language Task
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"task":"Google에서 browser automation 검색하기"}' \
  http://localhost:5001/execute
```

### Get Status
```bash
curl http://localhost:5001/status
```

### Get Task Examples
```bash
curl http://localhost:5001/tasks/examples
```

## 🧪 Testing

Run the automated test suite:
```bash
./test-api.sh
```

## 🛠 Environment Variables

- `DISPLAY=:99` - X11 display server
- `OPENAI_API_KEY` - Required for AI functionality (set when running container)

## 💡 Example Usage

### Simple Task Execution
```bash
# Navigate to a website
curl -X POST -H "Content-Type: application/json" \
  -d '{"task":"GitHub 홈페이지로 이동하기"}' \
  http://localhost:5001/execute

# Search on Google
curl -X POST -H "Content-Type: application/json" \
  -d '{"task":"Google에서 Playwright 검색하기"}' \
  http://localhost:5001/execute

# Extract information
curl -X POST -H "Content-Type: application/json" \
  -d '{"task":"현재 페이지의 제목과 주요 내용 요약하기"}' \
  http://localhost:5001/execute
```

### With OpenAI API Key
```bash
docker run -d --name magentic-ui-browser-use \
  -p 6080:6080 -p 37367:37367 -p 5001:5001 \
  -e OPENAI_API_KEY="your-api-key-here" \
  magentic-ui-browser-use
```

## 🔍 Debugging

### View Container Logs
```bash
docker logs -f magentic-ui-browser-use-test
```

### Connect to Container
```bash
docker exec -it magentic-ui-browser-use-test bash
```

### Check Service Status
```bash
# Inside container
supervisorctl status
```

## 📁 File Structure

```
docker/magentic-ui-browser-use-docker/
├── Dockerfile              # Main container definition
├── browser-use-server.py   # Browser-Use API server
├── supervisord.conf        # Service management
├── playwright-server.js    # Playwright WebSocket server
├── quick-build.sh         # Quick build and run script
├── test-api.sh            # API testing script
└── README.md              # This file
```

## 🐛 Troubleshooting

### Container Won't Start
1. Check Docker is running
2. Ensure ports 5001, 6080, 37367 are available
3. Check container logs: `docker logs container-name`

### API Not Responding
1. Wait 10-15 seconds after container start
2. Check health endpoint: `curl http://localhost:5001/health`
3. Verify container is running: `docker ps`

### Browser-Use Tasks Failing
1. Ensure OPENAI_API_KEY is set
2. Check if task is too complex
3. Try simpler tasks first
4. Check container logs for detailed error messages

## 🔗 Integration

This container can be integrated with:
- **Magentic UI**: Use the docker-manager.js API endpoints
- **External Applications**: Direct HTTP API calls
- **CI/CD Pipelines**: Automated browser testing

### Docker Manager Integration
```javascript
// Build Browser-Use Docker image
POST /api/browser-use-docker/build

// Start Browser-Use container
POST /api/browser-use-docker/start

// Check health
GET /api/browser-use-docker/health

// Execute task
POST /api/browser-use-docker/execute
```
