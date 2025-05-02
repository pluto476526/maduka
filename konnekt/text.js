// nav sidebar


<script>
document.addEventListener("DOMContentLoaded", () => {
    const userId = "{{ request.user.id }}";
    const recentChatsSocket = new WebSocket(`ws://${window.location.host}/ws/konnekt/recent-chats/${userId}/`);

    recentChatsSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const chats = data.recent_chats;
        const container = document.getElementById("recent_chats_list");
        container.innerHTML = "";

        chats.forEach(chat => {
            const li = document.createElement("li");
            li.className = chat.is_group ? "" : "online";

            let content = `
            <div class="hover_action">
                ${chat.is_group ? `
                <button class="btn btn-link text-info"><i class="zmdi zmdi-eye"></i></button>
                <button class="btn btn-link text-warning"><i class="zmdi zmdi-star"></i></button>
                ` : ""}
                <button class="btn btn-link text-danger"><i class="zmdi zmdi-delete"></i></button>
            </div>
            <a href="/konnekt/${chat.conv_id}/" class="card">
                <div class="card-body">
                    <div class="media">
                        <div class="avatar me-3">
                            <span class="status rounded-circle"></span>`;

            if (chat.is_group) {
                content += `
                    <div class="avatar rounded-circle no-image cyan">
                        <span>${chat.title ? chat.title.slice(0, 2).toUpperCase() : "GR"}</span>
                    </div>`;
            } else {
                content += `<img class="avatar rounded-circle" src="${chat.participants[0]?.avatar_url}" alt="avatar" style="object-fit: cover;">`;
            }

            content += `
                        </div>
                        <div class="media-body overflow-hidden">
                            <div class="d-flex align-items-center mb-1">
                                <h6 class="text-truncate mb-0 me-auto">${chat.is_group ? chat.title : chat.participants[0]?.username}</h6>
                                <p class="small text-muted text-nowrap ms-4 mb-0">${chat.timestamp}</p>
                            </div>
                            <div class="text-truncate">${chat.last_message}</div>`;

            if (chat.is_group) {
                content += `<div class="avatar-list avatar-list-stacked mt-1">`;
                chat.participants.forEach(p => {
                    content += `<img class="avatar xs rounded" src="${p.avatar_url}" data-toggle="tooltip" title="${p.username}">`;
                });
                content += `</div>`;
            }

            content += `</div></div></div></a>`;
            li.innerHTML = content;
            container.appendChild(li);
        });
    };

    recentChatsSocket.onclose = () => {
        console.error("WebSocket for recent chats closed");
    };
});
</script>











// chat 


<script>

	const wsUrl = `ws://${window.location.host}/ws/konnekt/{{ convo_id }}/`


	// Establish the WebSocket connection
	const chatSocket = new WebSocket(wsUrl);

  const msgForm = document.getElementById('msgForm')
  const msgBox = document.getElementById('msgBox')
  const sendBtn = document.getElementById('sendBtn')
  const chatBox = document.getElementById('chatBox')
  const chatItem = document.getElementById('chatItem')
  const senderAvatar = '{{ sender.profile.avatar.url }}'


  const scrollToBottom = () => {
    chatBox.scrollTop = chatBox.scrollHeight;
  }


  window.addEventListener('load', function () {
    // Give the DOM a slight delay to ensure content (e.g., images) is fully loaded
    setTimeout(() => {
      if (chatBox) {
        scrollToBottom();
      }
    }, 100);
  });


  // Async function to handle sending the message
  async function sendMessage() {
      const message = msgBox.value.trim();
      if (!message) return;

      try {
          chatSocket.send(JSON.stringify({
              'message': message,
              'convo_id': '{{ convo_id }}',
              'sender_id': '{{ request.user.id }}',
              'sender': '{{ request.user.username }}',
              'timestamp': Date.now(),
          }));
          msgBox.value = '';
      } catch (error) {
          console.error('Failed to send message:', error)
      }
  }

  // Send message on button click
  sendBtn.addEventListener('click', async function(event) {
      event.preventDefault();
      await sendMessage();
  });

  // Send message when pressing 'Enter' (without Shift)
  msgBox.addEventListener('keypress', async function(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          await sendMessage();
      }
  });


  chatSocket.addEventListener('message', (event) => {
    const data = JSON.parse(event.data)
    const sender = data['sender']
    const message = data['message']
    const sender_id = data['sender_id']
    const timestamp = data['timestamp']
    const s_time = new Date(timestamp).toLocaleString()

    if (sender_id == '{{request.user.id}}') {
      msgBox.value = '';
      chatItem.innerHTML += `<li class="d-flex message right"><div class="message-body"><span class="date-time text-muted">${s_time}<i class="zmdi zmdi-check-all text-primary"></i></span><div class="message-row d-flex align-items-center justify-content-end"><div class="dropdown"><a class="text-muted me-1 p-2 text-muted" href="#" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><i class="zmdi zmdi-more-vert"></i></a><div class="dropdown-menu"><a class="dropdown-item" href="#">Edit</a><a class="dropdown-item" href="#">Share</a><a class="dropdown-item" href="#">Delete</a></div></div><div class="message-content border p-3">${message}</div></div></div></li>`;
    } else {
      chatItem.innerHTML += `<li class="d-flex message"><div class="mr-lg-3 me-2"><img class="avatar sm rounded-circle" src="${senderAvatar}" alt="avatar" style="object-fit: cover;"></div><div class="message-body"><span class="date-time text-muted">${sender}, ${s_time}</span><div class="message-row d-flex align-items-center"><div class="message-content p-3">${message}</div><div class="dropdown"><a class="text-muted ms-1 p-2 text-muted" href="#" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><i class="zmdi zmdi-more-vert"></i></a><div class="dropdown-menu dropdown-menu-right"><a class="dropdown-item" href="#">Edit</a><a class="dropdown-item" href="#">Share</a><a class="dropdown-item" href="#">Delete</a></div></div></div></div></li>`;
    }

    scrollToBottom();
  });
</script>





/// main

  <script>
   //const onlineSocket = new WebSocket(`ws://${window.location.host}/ws/konnekt/online/`);

   // static/js/profileStatusSocket.js
  (function () {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socketUrl = `${protocol}://${window.location.host}/ws/konnekt/status/`;

    let socket;
    let pingInterval;
    let activityTimeout;

    function sendMessage(data) {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(data));
      }
    }

    function setupHeartbeat() {
      pingInterval = setInterval(() => {
        sendMessage({ type: "ping" });
      }, 30000);
    }

    function setupUserActivity() {
      const activityHandler = () => {
        if (activityTimeout) clearTimeout(activityTimeout);
        activityTimeout = setTimeout(() => {
          sendMessage({ type: "activity" });
        }, 500);
      };

      window.addEventListener('mousemove', activityHandler);
      window.addEventListener('keydown', activityHandler);
      window.addEventListener('scroll', activityHandler);
    }

    function connectSocket() {
      socket = new WebSocket(socketUrl);

      socket.onopen = () => {
        console.log("WebSocket connected.");
        sendMessage({ type: "activity" });
        setupHeartbeat();
      };

      socket.onclose = () => {
        console.warn("WebSocket closed. Reconnecting...");
        clearInterval(pingInterval);
        setTimeout(connectSocket, 2000);
      };

      socket.onerror = (err) => {
        console.error("WebSocket error:", err);
        socket.close();
      };

      setupUserActivity();
    }

    connectSocket();
  })();

  </script>
