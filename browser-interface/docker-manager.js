/**
 * Docker Container Manager for Magentic UI Browser
 * 이 스크립트는 Node.js 서버에서 실행되어 Docker 컨테이너를 관리합니다.
 */

const { exec, spawn } = require('child_process');
const express = require('express');
const path = require('path');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

// 미들웨어 설정
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

// Docker 이미지 및 컨테이너 설정
const DOCKER_IMAGE = 'magentic-ui-browser:latest';
const DOCKER_BUILD_PATH = '../docker/magentic-ui-browser-docker';

// Browser-Use Docker 설정
const BROWSER_USE_DOCKER_IMAGE = 'magentic-ui-browser-use:latest';
const BROWSER_USE_DOCKER_BUILD_PATH = '../docker/magentic-ui-browser-use-docker';

let containerInfo = {
    name: null,
    id: null,
    status: 'stopped',
    ports: {
        vnc: null,
        playwright: null
    }
};

/**
 * Docker 명령어 실행 함수
 */
function executeDockerCommand(command, options = {}) {
    return new Promise((resolve, reject) => {
        exec(command, options, (error, stdout, stderr) => {
            if (error) {
                reject({ error, stderr });
                return;
            }
            resolve({ stdout, stderr });
        });
    });
}

/**
 * Docker 이미지 빌드
 */
async function buildDockerImage() {
    try {
        console.log('Docker 이미지 빌드 시작...');
        const buildCommand = `cd ${DOCKER_BUILD_PATH} && docker build -t ${DOCKER_IMAGE} .`;
        const result = await executeDockerCommand(buildCommand);
        console.log('Docker 이미지 빌드 완료');
        return { success: true, output: result.stdout };
    } catch (error) {
        console.error('Docker 이미지 빌드 실패:', error);
        throw error;
    }
}

/**
 * 컨테이너 시작
 */
async function startContainer(containerName, vncPort, playwrightPort) {
    try {
        // 기존 컨테이너가 있다면 제거
        await stopContainer(containerName, false);
        
        const dockerCommand = [
            'docker', 'run', '-d',
            '--name', containerName,
            '-p', `${vncPort}:6080`,
            '-p', `${playwrightPort}:37367`,
            '-e', `NO_VNC_PORT=6080`,
            '-e', `PLAYWRIGHT_PORT=${playwrightPort}`,
            '-e', 'PLAYWRIGHT_WS_PATH=default',
            '--rm',
            DOCKER_IMAGE
        ].join(' ');

        console.log('컨테이너 시작 명령어:', dockerCommand);
        const result = await executeDockerCommand(dockerCommand);
        
        const containerId = result.stdout.trim();
        
        containerInfo = {
            name: containerName,
            id: containerId,
            status: 'running',
            ports: {
                vnc: vncPort,
                playwright: playwrightPort
            }
        };

        console.log('컨테이너 시작 완료:', containerInfo);
        return containerInfo;
    } catch (error) {
        console.error('컨테이너 시작 실패:', error);
        throw error;
    }
}

/**
 * 컨테이너 중지
 */
async function stopContainer(containerName, remove = true) {
    try {
        // 컨테이너 중지
        try {
            await executeDockerCommand(`docker stop ${containerName}`);
            console.log(`컨테이너 ${containerName} 중지됨`);
        } catch (error) {
            // 컨테이너가 없거나 이미 중지된 경우 무시
        }

        // 컨테이너 제거
        if (remove) {
            try {
                await executeDockerCommand(`docker rm ${containerName}`);
                console.log(`컨테이너 ${containerName} 제거됨`);
            } catch (error) {
                // 컨테이너가 없는 경우 무시
            }
        }

        containerInfo = {
            name: null,
            id: null,
            status: 'stopped',
            ports: {
                vnc: null,
                playwright: null
            }
        };

        return { success: true };
    } catch (error) {
        console.error('컨테이너 중지 실패:', error);
        throw error;
    }
}

/**
 * 컨테이너 상태 확인
 */
async function getContainerStatus(containerName) {
    try {
        const result = await executeDockerCommand(`docker ps -a --filter name=${containerName} --format "{{.Status}}"`);
        const status = result.stdout.trim();
        
        if (status && status.includes('Up')) {
            containerInfo.status = 'running';
        } else if (status) {
            containerInfo.status = 'stopped';
        } else {
            containerInfo.status = 'not_found';
        }
        
        return containerInfo;
    } catch (error) {
        console.error('컨테이너 상태 확인 실패:', error);
        containerInfo.status = 'error';
        return containerInfo;
    }
}

// API 엔드포인트

/**
 * Docker 이미지 빌드 API
 */
app.post('/api/build', async (req, res) => {
    try {
        const result = await buildDockerImage();
        res.json({ success: true, message: '이미지 빌드 완료', output: result.output });
    } catch (error) {
        res.status(500).json({ 
            success: false, 
            message: '이미지 빌드 실패', 
            error: error.error?.message || error.stderr 
        });
    }
});

/**
 * 컨테이너 시작 API
 */
app.post('/api/start', async (req, res) => {
    try {
        const { containerName = 'magentic-ui-browser', vncPort = 6080, playwrightPort = 37367 } = req.body;
        
        const result = await startContainer(containerName, vncPort, playwrightPort);
        res.json({ success: true, message: '컨테이너 시작 완료', container: result });
    } catch (error) {
        res.status(500).json({ 
            success: false, 
            message: '컨테이너 시작 실패', 
            error: error.error?.message || error.stderr 
        });
    }
});

/**
 * 컨테이너 중지 API
 */
app.post('/api/stop', async (req, res) => {
    try {
        const { containerName = 'magentic-ui-browser' } = req.body;
        
        await stopContainer(containerName);
        res.json({ success: true, message: '컨테이너 중지 완료' });
    } catch (error) {
        res.status(500).json({ 
            success: false, 
            message: '컨테이너 중지 실패', 
            error: error.error?.message || error.stderr 
        });
    }
});

/**
 * 컨테이너 재시작 API
 */
app.post('/api/restart', async (req, res) => {
    try {
        const { containerName = 'magentic-ui-browser', vncPort = 6080, playwrightPort = 37367 } = req.body;
        
        await stopContainer(containerName);
        
        // 잠시 대기 후 재시작
        setTimeout(async () => {
            try {
                const result = await startContainer(containerName, vncPort, playwrightPort);
                res.json({ success: true, message: '컨테이너 재시작 완료', container: result });
            } catch (error) {
                res.status(500).json({ 
                    success: false, 
                    message: '컨테이너 재시작 실패', 
                    error: error.error?.message || error.stderr 
                });
            }
        }, 2000);
    } catch (error) {
        res.status(500).json({ 
            success: false, 
            message: '컨테이너 재시작 실패', 
            error: error.error?.message || error.stderr 
        });
    }
});

/**
 * 컨테이너 상태 확인 API
 */
app.get('/api/status/:containerName?', async (req, res) => {
    try {
        const containerName = req.params.containerName || 'magentic-ui-browser';
        const status = await getContainerStatus(containerName);
        res.json({ success: true, container: status });
    } catch (error) {
        res.status(500).json({ 
            success: false, 
            message: '상태 확인 실패', 
            error: error.message 
        });
    }
});

/**
 * Docker 이미지 존재 확인 API
 */
app.get('/api/image/check', async (req, res) => {
    try {
        const result = await executeDockerCommand(`docker images ${DOCKER_IMAGE} --format "{{.Repository}}:{{.Tag}}"`);
        const exists = result.stdout.trim() === DOCKER_IMAGE;
        
        res.json({ 
            success: true, 
            exists, 
            image: DOCKER_IMAGE,
            message: exists ? '이미지가 존재합니다' : '이미지를 빌드해야 합니다'
        });
    } catch (error) {
        res.status(500).json({ 
            success: false, 
            message: '이미지 확인 실패', 
            error: error.error?.message || error.stderr 
        });
    }
});

/**
 * 브라우저 시작 API
 */
app.post('/api/browser/start', async (req, res) => {
    try {
        const { url = 'https://www.google.com' } = req.body;
        
        // Playwright를 사용해 브라우저 시작
        const { chromium } = require('playwright');
        
        // 원격 브라우저에 연결
        const browser = await chromium.connect('ws://localhost:37367/default');
        const page = await browser.newPage();
        
        await page.goto(url);
        
        res.json({ 
            success: true, 
            message: '브라우저가 성공적으로 시작되었습니다',
            url: url
        });
    } catch (error) {
        console.error('브라우저 시작 실패:', error);
        res.status(500).json({ 
            success: false, 
            message: '브라우저 시작 실패', 
            error: error.message 
        });
    }
});

/**
 * 브라우저 페이지 이동 API
 */
app.post('/api/browser/navigate', async (req, res) => {
    try {
        const { url } = req.body;
        
        if (!url) {
            return res.status(400).json({
                success: false,
                message: 'URL이 필요합니다'
            });
        }
        
        const { chromium } = require('playwright');
        
        const browser = await chromium.connect('ws://localhost:37367/default');
        const pages = await browser.contexts()[0].pages();
        
        if (pages.length === 0) {
            const page = await browser.newPage();
            await page.goto(url);
        } else {
            await pages[0].goto(url);
        }
        
        res.json({ 
            success: true, 
            message: '페이지 이동 완료',
            url: url
        });
    } catch (error) {
        console.error('페이지 이동 실패:', error);
        res.status(500).json({ 
            success: false, 
            message: '페이지 이동 실패', 
            error: error.message 
        });
    }
});

/**
 * 브라우저 스크린샷 API
 */
app.get('/api/browser/screenshot', async (req, res) => {
    try {
        const { chromium } = require('playwright');
        
        const browser = await chromium.connect('ws://localhost:37367/default');
        const pages = await browser.contexts()[0].pages();
        
        if (pages.length === 0) {
            return res.status(400).json({
                success: false,
                message: '활성화된 페이지가 없습니다'
            });
        }
        
        const screenshot = await pages[0].screenshot({ 
            type: 'png',
            fullPage: false
        });
        
        res.setHeader('Content-Type', 'image/png');
        res.send(screenshot);
    } catch (error) {
        console.error('스크린샷 실패:', error);
        res.status(500).json({ 
            success: false, 
            message: '스크린샷 실패', 
            error: error.message 
        });
    }
});

/**
 * Browser-Use 서버 상태 확인 API
 */
app.get('/api/browser-use/health', async (req, res) => {
    try {
        const response = await axios.get('http://127.0.0.1:5001/health');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Browser-Use 서버에 연결할 수 없습니다',
            error: error.message
        });
    }
});

/**
 * Browser-Use 브라우저 연결 API
 */
app.post('/api/browser-use/connect', async (req, res) => {
    try {
        const response = await axios.post('http://127.0.0.1:5001/connect', {
            ws_url: 'ws://localhost:37367/default'
        });
        
        res.json(response.data);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Browser-Use 연결 실패',
            error: error.message
        });
    }
});

/**
 * Browser-Use 자연어 태스크 실행 API
 */
app.post('/api/browser-use/execute', async (req, res) => {
    try {
        const { task } = req.body;
        
        if (!task) {
            return res.status(400).json({
                success: false,
                message: '태스크가 제공되지 않았습니다'
            });
        }
        
        const response = await axios.post('http://127.0.0.1:5001/execute', { task });
        
        res.json(response.data);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '태스크 실행 실패',
            error: error.message
        });
    }
});

/**
 * Browser-Use 태스크 예시 API
 */
app.get('/api/browser-use/examples', async (req, res) => {
    try {
        const response = await axios.get('http://127.0.0.1:5001/tasks/examples');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '예시 목록 조회 실패',
            error: error.message
        });
    }
});

/**
 * Browser-Use 페이지 정보 API
 */
app.get('/api/browser-use/page-info', async (req, res) => {
    try {
        const response = await axios.get('http://127.0.0.1:5001/page_info');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: '페이지 정보 조회 실패',
            error: error.message
        });
    }
});

/**
 * Browser-Use Docker 이미지 빌드 API
 */
app.post('/api/browser-use-docker/build', async (req, res) => {
    try {
        console.log('Browser-Use Docker 이미지 빌드 시작...');
        const buildCommand = `cd ${BROWSER_USE_DOCKER_BUILD_PATH} && docker build -t ${BROWSER_USE_DOCKER_IMAGE} .`;
        const result = await executeDockerCommand(buildCommand);
        console.log('Browser-Use Docker 이미지 빌드 완료');
        res.json({ success: true, message: 'Browser-Use 이미지 빌드 완료', output: result.stdout });
    } catch (error) {
        console.error('Browser-Use Docker 이미지 빌드 실패:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Browser-Use 이미지 빌드 실패', 
            error: error.error?.message || error.stderr 
        });
    }
});

/**
 * Browser-Use Docker 컨테이너 시작 API
 */
app.post('/api/browser-use-docker/start', async (req, res) => {
    try {
        const { containerName = 'magentic-ui-browser-use', vncPort = 6080, playwrightPort = 37367, browserUsePort = 5001 } = req.body;
        
        // 기존 컨테이너가 있다면 제거
        await stopContainer(containerName, false);
        
        const dockerCommand = [
            'docker', 'run', '-d',
            '--name', containerName,
            '-p', `${vncPort}:6080`,
            '-p', `${playwrightPort}:37367`,
            '-p', `${browserUsePort}:5001`,
            '-e', `NO_VNC_PORT=6080`,
            '-e', `PLAYWRIGHT_PORT=${playwrightPort}`,
            '-e', 'PLAYWRIGHT_WS_PATH=default',
            '--rm',
            BROWSER_USE_DOCKER_IMAGE
        ].join(' ');

        console.log('Browser-Use 컨테이너 시작 명령어:', dockerCommand);
        const result = await executeDockerCommand(dockerCommand);
        
        const containerId = result.stdout.trim();
        
        const browserUseContainerInfo = {
            name: containerName,
            id: containerId,
            status: 'running',
            ports: {
                vnc: vncPort,
                playwright: playwrightPort,
                browserUse: browserUsePort
            }
        };

        console.log('Browser-Use 컨테이너 시작 완료:', browserUseContainerInfo);
        res.json({ success: true, message: 'Browser-Use 컨테이너 시작 완료', container: browserUseContainerInfo });
    } catch (error) {
        console.error('Browser-Use 컨테이너 시작 실패:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Browser-Use 컨테이너 시작 실패', 
            error: error.error?.message || error.stderr 
        });
    }
});

/**
 * Browser-Use Docker API 상태 확인
 */
app.get('/api/browser-use-docker/health', async (req, res) => {
    try {
        const response = await axios.get('http://127.0.0.1:5001/health');
        res.json(response.data);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Browser-Use Docker 서버에 연결할 수 없습니다',
            error: error.message
        });
    }
});

/**
 * Browser-Use Docker 태스크 실행 API
 */
app.post('/api/browser-use-docker/execute', async (req, res) => {
    try {
        const { task } = req.body;
        
        if (!task) {
            return res.status(400).json({
                success: false,
                message: '태스크가 제공되지 않았습니다'
            });
        }
        
        const response = await axios.post('http://127.0.0.1:5001/execute', { task });
        
        res.json(response.data);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Browser-Use Docker 태스크 실행 실패',
            error: error.message
        });
    }
});

// noVNC 프록시 설정
app.use('/vnc', createProxyMiddleware({
    target: 'http://localhost:6080',
    changeOrigin: true,
    pathRewrite: {
        '^/vnc': '',
    },
    ws: true, // WebSocket 지원
    onError: (err, req, res) => {
        console.error('Proxy error:', err.message);
        res.status(500).json({ 
            success: false, 
            message: 'VNC 프록시 오류', 
            error: err.message 
        });
    }
}));

// 정적 파일 서빙
app.use(express.static(__dirname));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'enhanced-index.html'));
});

// 서버 시작
app.listen(PORT, () => {
    console.log(`🚀 Magentic UI Browser Interface 서버가 포트 ${PORT}에서 실행 중입니다.`);
    console.log(`📱 웹 인터페이스: http://localhost:${PORT}`);
    console.log(`🐳 Docker 이미지: ${DOCKER_IMAGE}`);
    console.log(`📁 빌드 경로: ${DOCKER_BUILD_PATH}`);
});

// 종료 시 정리
process.on('SIGINT', async () => {
    console.log('\n서버를 종료합니다...');
    if (containerInfo.status === 'running') {
        console.log('실행 중인 컨테이너를 중지합니다...');
        await stopContainer(containerInfo.name);
    }
    process.exit(0);
});

module.exports = app;
