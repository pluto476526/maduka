
document.addEventListener("DOMContentLoaded", () => {
    const chatListElement = document.getElementById("recent_chats_list");
    const userId = chatListElement.dataset.userId;

    if (!userId) {
        console.error("User ID not found in DOM.");
        return;
    } else {
        console.log('fuck')
    }
    const recentChatsSocket = new WebSocket(`ws://${window.location.host}/ws/konnekt/recent-chats/${userId}/`);
    const statusSocket = new WebSocket(`${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/status/`);



    const debounceMap = {};
    const userStatusMap = {};  // For tracking online status across chats

    function debounceUpdate(userId, updateFn, delay = 500) {
        if (debounceMap[userId]) clearTimeout(debounceMap[userId]);
        debounceMap[userId] = setTimeout(() => {
            updateFn();
            delete debounceMap[userId];
        }, delay);
    }

    function naturalTimeFormat(value) {
        const date = new Date(value);
        if (isNaN(date)) return "Invalid date";

        const now = new Date();
        const delta = (now - date) / 1000;

        if (delta < 60) return "Just now";
        if (delta < 3600) return `${Math.floor(delta / 60)} min ago`;
        if (delta < 86400) return `${Math.floor(delta / 3600)} hr ago`;
        if (delta < 172800) return "Yesterday";
        if (delta < 604800) return `${Math.floor(delta / 86400)} days ago`;

        return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function renderRecentChats(chats) {
        const container = document.getElementById("recent_chats_list");
        container.innerHTML = "";

        chats.forEach(chat => {
            const li = document.createElement("li");
            li.id = `chat-${chat.conv_id}`;
            li.className = "chat-entry";

            let participantAvatars = '';
            let statusDots = '';
            let participantNames = [];

            chat.participants.forEach(p => {
                participantNames.push(p.username);

                const dotId = `dot-${p.userID}`;
                const containerId = `container-${chat.conv_id}-${p.userID}`;

                const dotStatus = userStatusMap[p.userID]?.status === 'online' ? `<span class="status rounded-circle" id="${dotId}"></span>` : '';

                statusDots += `
                    <div class="avatar me-1" id="${containerId}">
                        ${dotStatus}
                        <img class="avatar rounded-circle" src="${p.avatar_url}" style="object-fit: cover;" alt="${p.username}">
                    </div>
                `;
            });

            const lastMessageTime = naturalTimeFormat(chat.last_message_timestamp || chat.timestamp);

            li.innerHTML = `
                <a href="/konnekt/${chat.conv_id}/" class="card">
                    <div class="card-body">
                        <div class="media align-items-center">
                            <div class="d-flex align-items-center me-3">
                                ${statusDots}
                            </div>
                            <div class="media-body overflow-hidden">
                                <div class="d-flex align-items-center mb-1">
                                    <h6 class="text-truncate mb-0 me-auto">${chat.is_group ? chat.title : participantNames.join(', ')}</h6>
                                    <p class="small text-muted text-nowrap ms-4 mb-0">${lastMessageTime}</p>
                                </div>
                                <div class="text-truncate">${chat.last_message || "No messages yet"}</div>
                            </div>
                        </div>
                    </div>
                </a>
            `;
            container.appendChild(li);
        });
    }

    // Handle chat list updates
    recentChatsSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const chats = data.recent_chats;
        renderRecentChats(chats);
    };

    // Handle status updates
    statusSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (!data.user_id) return;

        userStatusMap[data.user_id] = {
            status: data.status,
            last_seen: data.last_seen
        };

        debounceUpdate(data.user_id, () => {
            const dotId = `dot-${data.user_id}`;
            const newDot = document.createElement('span');
            newDot.className = 'status rounded-circle';
            newDot.id = dotId;

            document.querySelectorAll(`[id^="container-"][id$="-${data.user_id}"]`).forEach(container => {
                const oldDot = container.querySelector(`#${dotId}`);
                if (data.status === "online") {
                    if (!oldDot) container.prepend(newDot.cloneNode());
                } else if (oldDot) {
                    oldDot.remove();
                }
            });
        });
    };

    statusSocket.onclose = () => console.warn("Status socket closed");
    statusSocket.onerror = err => console.error("Status socket error", err);
});
