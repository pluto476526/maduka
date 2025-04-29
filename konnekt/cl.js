<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat</title>
    <style>
        /* Add some basic styles */
        #messages {
            border: 1px solid #ccc;
            height: 300px;
            overflow-y: auto;
        }
        #message-input {
            width: 100%;
            padding: 10px;
        }
    </style>
</head>
<body>
    <h2>Chat Room</h2>
    <div id="messages"></div>
    <textarea id="message-input" placeholder="Type a message..." rows="3"></textarea>
    <button id="send-btn">Send</button>

    <script>
        const convId = 'your_conversation_id';  // Replace with your dynamic conversation ID
        const wsUrl = `ws://${window.location.host}/ws/chat/${convId}/`;  // WebSocket URL
        
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');

        // Establish the WebSocket connection
        const chatSocket = new WebSocket(wsUrl);

        // Handle messages from the server
        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            const message = data.message;
            // Append the new message to the messages div
            messagesDiv.innerHTML += `<p>${message}</p>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;  // Scroll to the bottom
        };

        // Handle WebSocket connection open
        chatSocket.onopen = function() {
            console.log('WebSocket connection established');
        };

        // Handle WebSocket connection close
        chatSocket.onclose = function(e) {
            console.log('WebSocket connection closed: ' + e.code);
        };

        // Handle errors
        chatSocket.onerror = function(e) {
            console.error('WebSocket error: ' + e);
        };

        // Send message on button click
        sendBtn.onclick = function() {
            const message = messageInput.value;
            if (message) {
                chatSocket.send(JSON.stringify({
                    'message': message
                }));
                messageInput.value = '';  // Clear the input field
            }
        };

        // Optionally, send a message when pressing 'Enter'
        messageInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                sendBtn.click();
                event.preventDefault();  // Prevent newline on 'Enter'
            }
        });
    </script>
</body>
</html>

