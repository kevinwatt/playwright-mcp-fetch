import EventSource from 'eventsource';
import fetch from 'node-fetch';

// 創建 SSE 連接
const eventSource = new EventSource('http://localhost:3001/sse');

console.log('Connecting to SSE endpoint...');

// 監聽連接打開事件
eventSource.onopen = () => {
  console.log('Connection opened');
  
  // 連接成功後，發送一個工具調用請求
  setTimeout(() => {
    console.log('Sending tool call request...');
    fetch('http://localhost:3001/api/call-tool', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: 'fetch_txt',
        arguments: {
          url: 'https://example.com'
        }
      })
    })
    .then(response => response.json())
    .then(data => console.log('Tool call response:', data))
    .catch(error => console.error('Error calling tool:', error));
  }, 1000);
};

// 監聽消息事件
eventSource.onmessage = (event) => {
  console.log('Received message:', event.data);
};

// 監聽特定事件
eventSource.addEventListener('tool-result', (event) => {
  console.log('Tool result received:', event.data);
  try {
    const result = JSON.parse(event.data);
    console.log('Parsed result:', result);
  } catch (error) {
    console.error('Error parsing result:', error);
  }
});

// 監聽錯誤
eventSource.onerror = (error) => {
  console.error('SSE error:', error);
};

// 30 秒後關閉連接
setTimeout(() => {
  console.log('Closing connection...');
  eventSource.close();
  process.exit(0);
}, 30000); 