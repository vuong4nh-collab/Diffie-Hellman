// Diffie-Hellman Web UI Logic
document.addEventListener("DOMContentLoaded", () => {
    // === DOM ELEMENTS ===
    const modeSelect = document.getElementById("modeSelect");
    const roleSelectGroup = document.getElementById("roleSelectGroup");
    const roleSelect = document.getElementById("roleSelect");
    const connectionStatus = document.getElementById("connectionStatus");
    const connectBtn = document.getElementById("connectBtn");
    const resetBtn = document.getElementById("resetBtn");
    
    // Parameter boxes
    const boxP = document.getElementById("box-p");
    const boxG = document.getElementById("box-g");
    const boxA = document.getElementById("box-A");
    const boxB = document.getElementById("box-B");
    const boxK = document.getElementById("box-K");
    
    // Parameter value text areas
    const valP = document.getElementById("param-p-val");
    const valG = document.getElementById("param-g-val");
    const valA = document.getElementById("param-A-val");
    const valB = document.getElementById("param-B-val");
    const valK = document.getElementById("param-K-val");
    
    // Logs & Chat
    const logsContainer = document.getElementById("logsContainer");
    const viewAuditLogBtn = document.getElementById("viewAuditLogBtn");
    const channelHeader = document.getElementById("channelHeader");
    const channelHeaderText = document.getElementById("channelHeaderText");
    const tunnelScreen = document.getElementById("tunnelScreen");
    const simStepsContainer = document.getElementById("simStepsContainer");
    const simStep1Btn = document.getElementById("simStep1Btn");
    const simStep2Btn = document.getElementById("simStep2Btn");
    const simStep3Btn = document.getElementById("simStep3Btn");
    const chatScreen = document.getElementById("chatScreen");
    const chatMessages = document.getElementById("chatMessages");
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    
    // Eve's View
    const tabEveBtn = document.getElementById("tabEveBtn");
    const tabDebugBtn = document.getElementById("tabDebugBtn");
    const tabContentEve = document.getElementById("tabContentEve");
    const tabContentDebug = document.getElementById("tabContentDebug");
    const packetsList = document.getElementById("packetsList");
    const entropyChart = document.getElementById("entropyChart");
    const decryptAttempts = document.getElementById("decryptAttempts");
    const decryptProb = document.getElementById("decryptProb");
    
    // Modal
    const auditLogModal = document.getElementById("auditLogModal");
    const modalLogsContainer = document.getElementById("modalLogsContainer");
    const closeModalBtn = document.getElementById("closeModalBtn");
    
    // Debug panel
    const debugDump = document.getElementById("debugDump");
    const debugAutoTalkBtn = document.getElementById("debugAutoTalkBtn");
    const debugForceKeyBtn = document.getElementById("debugForceKeyBtn");

    // Hand-Made mode elements
    const handmadeContainer = document.getElementById("handmadeContainer");
    const hmStep1Panel = document.getElementById("hmStep1Panel");
    const hmStep2Panel = document.getElementById("hmStep2Panel");
    const hmStep3Panel = document.getElementById("hmStep3Panel");
    const hmInputQ     = document.getElementById("hmInputQ");
    const hmInputAlpha = document.getElementById("hmInputAlpha");
    const hmInputXA    = document.getElementById("hmInputXA");
    const hmInputXB    = document.getElementById("hmInputXB");
    const hmStep1Btn   = document.getElementById("hmStep1Btn");
    const hmStep2Btn   = document.getElementById("hmStep2Btn");
    const hmStep3Btn   = document.getElementById("hmStep3Btn");
    const hmFormulaBlock = document.getElementById("hmFormulaBlock");

    // === SYSTEM VARIABLES ===
    let mode = "handmade"; // handmade, simulation or relay
    let socket = null;
    let isConnected = false;
    let myRole = "alice"; // alice or bob (for relay mode)
    
    // DH Parameters (256-bit prime p matching the mockup)
    const P_HEX = "ffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd1";
    const P_VAL = BigInt("0xffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd1");
    const G_VAL = 2n;
    
    // Cryptographic state variables
    let state = {
        p: null,
        g: null,
        a_priv: null, // Alice private key
        b_priv: null, // Bob private key
        A_pub: null,  // Alice public key
        B_pub: null,  // Bob public key
        sharedSecret: null,
        aesKey: null,
        packetCounter: 400
    };

    // Attempts decryption simulator variables
    let attemptsCount = 0;
    let attemptsInterval = null;

    // Entropy graph animation variables
    let entropyValues = Array(11).fill(75); // line chart points
    
    // === MATH HELPERS (BigInt Modular Exponentiation) ===
    function modPow(base, exponent, modulus) {
        if (modulus === 1n) return 0n;
        let result = 1n;
        base = base % modulus;
        while (exponent > 0n) {
            if (exponent % 2n === 1n) {
                result = (result * base) % modulus;
            }
            exponent = exponent / 2n;
            base = (base * base) % modulus;
        }
        return result;
    }

    function generatePrivateKey() {
        // Simple random generation suitable for demo/simulation
        let randHex = "";
        for (let i = 0; i < 48; i++) {
            randHex += Math.floor(Math.random() * 16).toString(16);
        }
        return BigInt("0x" + randHex) % (P_VAL - 3n) + 2n;
    }

    function getFingerprint(secret) {
        if (!secret) return "-";
        // Simple mock SHA-256 slice representation for visual aesthetics
        const secretStr = secret.toString(16);
        let hash = 0;
        for (let i = 0; i < secretStr.length; i++) {
            hash = (hash << 5) - hash + secretStr.charCodeAt(i);
            hash |= 0;
        }
        const hex = Math.abs(hash).toString(16).toUpperCase().padStart(8, "0");
        return `${hex.slice(0, 6)}... (Encrypted)`;
    }

    function formatHex(str) {
        // Add spaces for hex readability (like: FFFFFFFF FFFFFFFF...)
        if (!str) return "";
        str = str.replace(/0x/gi, "").toUpperCase();
        const chunks = str.match(/.{1,8}/g);
        return chunks ? chunks.join(" ") : str;
    }

    // Safe BigInt from hex string (with or without 0x prefix)
    function hexToBigInt(hexStr) {
        if (!hexStr) return null;
        const clean = hexStr.replace(/^0x/i, "");
        return BigInt("0x" + clean);
    }

    // === UI UTILITIES ===
    function addLog(type, message) {
        const time = new Date().toLocaleTimeString();
        const typeClass = `log-type-${type.toLowerCase()}`;
        const logHtml = `<div class="log-entry"><span class="log-time">[${time}]</span> <span class="${typeClass}">${type}</span>: ${message}</div>`;
        
        logsContainer.innerHTML += logHtml;
        logsContainer.scrollTop = logsContainer.scrollHeight;
        
        modalLogsContainer.innerHTML += logHtml;
        modalLogsContainer.scrollTop = modalLogsContainer.scrollHeight;
    }

    function setParamBoxState(box, stateClass) {
        box.classList.remove("active", "waiting");
        if (stateClass) {
            box.classList.add(stateClass);
        }
    }

    function updateDebugDump() {
        const isSmall = state.p && state.p < 100000n;
        const fmt = (v) => v === null ? "None" : (isSmall ? v.toString() : ("0x" + v.toString(16).slice(0, 16) + "..."));
        debugDump.innerText = `q         = ${state.p ? state.p.toString() : "None"}
α         = ${state.g ? state.g.toString() : "None"}
X_A (priv)= ${state.a_priv ? fmt(state.a_priv) : "None"}
X_B (priv)= ${state.b_priv ? fmt(state.b_priv) : "None"}
Y_A (pub) = ${state.A_pub ? fmt(state.A_pub) : "None"}
Y_B (pub) = ${state.B_pub ? fmt(state.B_pub) : "None"}
K_A = K_B = ${state.sharedSecret ? fmt(state.sharedSecret) : "None"}`;
    }

    // === EVE'S HACKER TERMINAL SIMULATORS ===
    function startDecryptSimulator() {
        if (attemptsInterval) clearInterval(attemptsInterval);
        attemptsCount = 0;
        decryptAttempts.innerText = "0";
        decryptProb.innerText = "< 0.000001%";
        
        attemptsInterval = setInterval(() => {
            if (state.sharedSecret) {
                // Increment attempts rapidly when tunnel is established
                attemptsCount += Math.floor(Math.random() * 250000) + 120000;
                decryptAttempts.innerText = attemptsCount.toLocaleString();
                
                // Set fake probability representing the cryptographic resistance
                decryptProb.innerText = `< 0.00000000${Math.floor(Math.random() * 9) + 1}%`;
            }
        }, 80);
    }

    function stopDecryptSimulator() {
        if (attemptsInterval) {
            clearInterval(attemptsInterval);
            attemptsInterval = null;
        }
    }

    function addInterceptedPacketUI(packetId, sender, receiver, dataType, payload, status) {
        const statusClass = status.includes("Insecure") ? "insecure" : "secure";
        const packetHtml = `
            <div class="packet-card">
                <div class="packet-header">
                    <span>Packet #${packetId}</span>
                    <span>${sender} &rarr; ${receiver}</span>
                </div>
                <div class="packet-data">
                    <strong>RAW_DATA:</strong> ${payload}
                </div>
                <div class="packet-status-tag ${statusClass}">[${status}]</div>
            </div>
        `;
        packetsList.innerHTML = packetHtml + packetsList.innerHTML;
        spikeEntropy();
    }

    // Entropy SVG line updates
    function updateEntropyChart() {
        const width = 300;
        const spacing = width / 10;
        
        // Generate svg points
        let dLine = `M 0,${entropyValues[0]}`;
        let dArea = `M 0,${entropyValues[0]}`;
        
        for (let i = 1; i < entropyValues.length; i++) {
            const x = i * spacing;
            dLine += ` L ${x},${entropyValues[i]}`;
            dArea += ` L ${x},${entropyValues[i]}`;
        }
        
        dArea += ` L 300,80 L 0,80 Z`;
        
        const pathLine = entropyChart.querySelector(".entropy-line");
        const pathArea = entropyChart.querySelector(".entropy-area");
        
        if (pathLine && pathArea) {
            pathLine.setAttribute("d", dLine);
            pathArea.setAttribute("d", dArea);
        }
    }

    function spikeEntropy() {
        // Insert a spikes in the entropy log
        for (let i = 5; i < 9; i++) {
            entropyValues[i] = Math.floor(Math.random() * 30) + 10; // high entropy peak (lower pixel value is higher up)
        }
        updateEntropyChart();
        
        // Return to normal baseline gradually
        setTimeout(() => {
            for (let i = 0; i < entropyValues.length; i++) {
                entropyValues[i] = Math.floor(Math.random() * 15) + 65; // baseline noise
            }
            updateEntropyChart();
        }, 600);
    }

    // Generate normal idle network noise
    setInterval(() => {
        if (!state.sharedSecret) {
            // Lower entropy prior to handshake
            for (let i = 0; i < entropyValues.length; i++) {
                entropyValues[i] = 75;
            }
        } else {
            // Idle background noise
            for (let i = 0; i < entropyValues.length; i++) {
                // drift slightly
                entropyValues[i] = Math.max(60, Math.min(78, entropyValues[i] + (Math.random() * 6 - 3)));
            }
        }
        updateEntropyChart();
    }, 300);

    // === SIMULATION MODE LOGIC ===
    function runSimStep1() {
        addLog("SYSTEM", "Bắt đầu khởi tạo các tham số Diffie-Hellman...");
        
        state.p = P_VAL;
        state.g = G_VAL;
        
        valP.value = formatHex(P_HEX);
        valG.value = G_VAL.toString();
        
        setParamBoxState(boxP, "active");
        setParamBoxState(boxG, "active");
        
        addLog("DH_PARAMS", "Số nguyên tố q (256-bit) và primitive root α = 2 được chọn.");
        
        // Generate Alice keys
        state.a_priv = generatePrivateKey();
        state.A_pub = modPow(state.g, state.a_priv, state.p);
        
        valA.value = formatHex(state.A_pub.toString(16));
        setParamBoxState(boxA, "active");
        
        addLog("PUB_KEY", `Alice tính: Y<sub>A</sub> = α<sup>X<sub>A</sub></sup> mod q.`);
        addLog("CONNECTION", "Alice gửi tham số q, α và Khóa Y<sub>A</sub> cho Bob...");
        
        state.packetCounter++;
        addInterceptedPacketUI(state.packetCounter, "Alice", "Bob", "DH_PARAMS", `q = ${P_HEX.slice(0, 16)}... α = 2`, "Insecure Phase");
        state.packetCounter++;
        addInterceptedPacketUI(state.packetCounter, "Alice", "Bob", "PUB_KEY_Y_A", `Y<sub>A</sub> = ${state.A_pub.toString(16).slice(0, 24)}...`, "Insecure Phase");
        
        simStep1Btn.disabled = true;
        simStep2Btn.disabled = false;
        setParamBoxState(boxB, "waiting");
        
        updateDebugDump();
    }

    function runSimStep2() {
        addLog("SYSTEM", "Bob nhận tham số từ Alice và phản hồi...");
        
        state.b_priv = generatePrivateKey();
        state.B_pub = modPow(state.g, state.b_priv, state.p);
        
        valB.value = formatHex(state.B_pub.toString(16));
        setParamBoxState(boxB, "active");
        
        addLog("PUB_KEY", `Bob tính: Y<sub>B</sub> = α<sup>X<sub>B</sub></sup> mod q và gửi lại cho Alice.`);
        
        state.packetCounter++;
        addInterceptedPacketUI(state.packetCounter, "Bob", "Alice", "PUB_KEY_Y_B", `Y<sub>B</sub> = ${state.B_pub.toString(16).slice(0, 24)}...`, "Insecure Phase");
        
        simStep2Btn.disabled = true;
        simStep3Btn.disabled = false;
        setParamBoxState(boxK, "waiting");
        
        updateDebugDump();
    }

    function runSimStep3() {
        addLog("SYSTEM", "Alice và Bob tính toán khóa bí mật chung...");
        
        const K_alice = modPow(state.B_pub, state.a_priv, state.p);
        const K_bob   = modPow(state.A_pub, state.b_priv, state.p);
        
        if (K_alice === K_bob) {
            state.sharedSecret = K_alice;
            valK.value = getFingerprint(state.sharedSecret);
            setParamBoxState(boxK, "active");
            
            addLog("PUB_KEY", `Alice tính: K<sub>A</sub> = (Y<sub>B</sub>)<sup>X<sub>A</sub></sup> mod q. Bob tính: K<sub>B</sub> = (Y<sub>A</sub>)<sup>X<sub>B</sub></sup> mod q.`);
            addLog("SYSTEM", "✅ Xác nhận: K<sub>A</sub> = K<sub>B</sub> — Khóa bí mật chung khớp hoàn toàn!");
            addLog("CONNECTION", "Đường truyền bảo mật AES-256-CBC được thiết lập thành công.");
            
            simStep3Btn.disabled = true;
            tunnelScreen.classList.add("hidden");
            chatScreen.classList.remove("hidden");
            
            channelHeader.style.backgroundColor = "var(--success-bg)";
            channelHeaderText.innerText = "Kênh Bảo Mật: Alice \u2194 Bob";
            channelHeaderText.style.color = "var(--success-text)";
            
            chatInput.disabled = false;
            sendBtn.disabled = false;
            
            connectionStatus.classList.remove("disconnected", "connecting");
            connectionStatus.classList.add("connected");
            connectionStatus.querySelector(".status-text").innerText = "CONNECTED";
            
            appendSystemMessage("Session Key established. Channel encrypted with AES-256-CBC.");
            startDecryptSimulator();
            updateDebugDump();
            
            setTimeout(() => {
                appendChatBubble("Bob", "Chào Alice, bạn đã nhận được các tham số DH chưa?", "a7f82b4c10ab88e1e813f0190a67e911");
                state.packetCounter++;
                addInterceptedPacketUI(state.packetCounter, "Bob", "Alice", "CIPHERTEXT", `PAYLOAD: 0x5846a19231201588... (IV: a7f82b4c...)`, "Encrypted - Key Unknown");
            }, 1000);
        } else {
            addLog("SYSTEM", "❌ Lỗi: Khóa bí mật chung không khớp!");
        }
    }

    function handleLocalSend() {
        const text = chatInput.value.trim();
        if (!text) return;
        
        // Append user Alice message
        const iv_alice = "c92d11e8a93bb1a2dcd448c901e129f1";
        appendChatBubble("Alice (Bạn)", text, iv_alice, true);
        chatInput.value = "";
        
        // Intercept packet (representing ciphertext)
        state.packetCounter++;
        const mockCipher = "a8f4c2810de08f23bb19a4e3210d7aef";
        addInterceptedPacketUI(state.packetCounter, "Alice", "Bob", "CIPHERTEXT", `PAYLOAD: 0x${mockCipher}... (IV: c92d11e8...)`, "Encrypted - Key Unknown");
        
        // Auto bot response
        setTimeout(() => {
            let reply = "Tuyệt vời. Hệ thống đang theo dõi mọi nỗ lực tấn công từ bên ngoài.";
            if (text.toLowerCase().includes("chào") || text.toLowerCase().includes("hello")) {
                reply = "Đã nhận. Shared Secret đã được tính toán xong. Bắt đầu truyền tin an toàn.";
            } else if (text.toLowerCase().includes("khóa") || text.toLowerCase().includes("key")) {
                reply = "Session Key của chúng ta cực kỳ an toàn. Kẻ nghe lén Eve sẽ không giải mã được.";
            }
            
            const iv_bob = "e7b8c2d131f49a883aefcde92a83f982";
            appendChatBubble("Bob", reply, iv_bob);
            
            state.packetCounter++;
            addInterceptedPacketUI(state.packetCounter, "Bob", "Alice", "CIPHERTEXT", `PAYLOAD: 0x27f1c84b1a108a9d... (IV: e7b8c2d1...)`, "Encrypted - Key Unknown");
        }, 1500);
    }

    // === CHAT BUBBLE RENDERERS ===
    function appendChatBubble(sender, text, iv, isRight = false) {
        const alignmentClass = isRight ? "right" : "left";
        const bubbleHtml = `
            <div class="message-bubble-wrapper ${alignmentClass}">
                <span class="message-sender">${sender}</span>
                <div class="message-bubble">${text}</div>
                <div class="message-metadata">IV: ${iv.slice(0, 16)}...</div>
            </div>
        `;
        chatMessages.innerHTML += bubbleHtml;
        chatMessages.scrollTop = chatMessages.scrollHeight;
        spikeEntropy();
    }

    function appendSystemMessage(text) {
        const msgHtml = `<div class="chat-notification">${text}</div>`;
        chatMessages.innerHTML += msgHtml;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // === HAND-MADE MODE LOGIC ===

    function runHmStep1() {
        // Clear previous errors
        [hmInputQ, hmInputAlpha, hmInputXA].forEach(el => el.classList.remove("error"));

        const qVal    = parseInt(hmInputQ.value, 10);
        const alphaVal = parseInt(hmInputAlpha.value, 10);
        const xAVal   = parseInt(hmInputXA.value, 10);

        let valid = true;
        if (!hmInputQ.value     || isNaN(qVal)    || qVal < 3)           { hmInputQ.classList.add("error");     valid = false; }
        if (!hmInputAlpha.value || isNaN(alphaVal) || alphaVal < 2)      { hmInputAlpha.classList.add("error"); valid = false; }
        if (!hmInputXA.value    || isNaN(xAVal)    || xAVal < 2 || xAVal >= qVal) { hmInputXA.classList.add("error"); valid = false; }

        if (!valid) {
            addLog("SYSTEM", "⚠️ Vui lòng kiểm tra lại giá trị nhập vào (q phải là số nguyên tố, Xₐ phải ≥ 2 và < q).");
            return;
        }

        state.p      = BigInt(qVal);
        state.g      = BigInt(alphaVal);
        state.a_priv = BigInt(xAVal);
        state.A_pub  = modPow(state.g, state.a_priv, state.p);

        // Update left sidebar
        valP.value = qVal.toString();
        valG.value = alphaVal.toString();
        valA.value = state.A_pub.toString();
        setParamBoxState(boxP, "active");
        setParamBoxState(boxG, "active");
        setParamBoxState(boxA, "active");
        setParamBoxState(boxB, "waiting");

        addLog("DH_PARAMS", `Tham số công khai: q = ${qVal}, α = ${alphaVal}`);
        addLog("PUB_KEY",  `Alice tính: Y<sub>A</sub> = α<sup>X<sub>A</sub></sup> mod q = ${alphaVal}<sup>${xAVal}</sup> mod ${qVal} = ${state.A_pub}`);
        addLog("CONNECTION", `Alice gửi (q, α, Y<sub>A</sub> = ${state.A_pub}) cho Bob qua kênh công khai.`);

        // Eve intercepts
        state.packetCounter++;
        addInterceptedPacketUI(state.packetCounter, "Alice", "Bob", "DH_PARAMS",  `q=${qVal}, α=${alphaVal}`, "Insecure Phase");
        state.packetCounter++;
        addInterceptedPacketUI(state.packetCounter, "Alice", "Bob", "PUB_KEY_Y_A", `Y<sub>A</sub> = ${state.A_pub}`, "Insecure Phase");

        // Advance to step 2
        hmStep1Panel.classList.add("hidden");
        hmStep2Panel.classList.remove("hidden");
        updateDebugDump();
    }

    function runHmStep2() {
        hmInputXB.classList.remove("error");
        const xBVal = parseInt(hmInputXB.value, 10);
        const qVal  = Number(state.p);

        if (!hmInputXB.value || isNaN(xBVal) || xBVal < 2 || xBVal >= qVal) {
            hmInputXB.classList.add("error");
            addLog("SYSTEM", `⚠️ Xʙ phải là số nguyên ≥ 2 và < q (= ${qVal}).`);
            return;
        }

        state.b_priv = BigInt(xBVal);
        state.B_pub  = modPow(state.g, state.b_priv, state.p);

        valB.value = state.B_pub.toString();
        setParamBoxState(boxB, "active");
        setParamBoxState(boxK, "waiting");

        addLog("PUB_KEY",  `Bob tính: Y<sub>B</sub> = α<sup>X<sub>B</sub></sup> mod q = ${state.g}<sup>${xBVal}</sup> mod ${state.p} = ${state.B_pub}`);
        addLog("CONNECTION", `Bob gửi Y<sub>B</sub> = ${state.B_pub} cho Alice qua kênh công khai.`);

        // Eve intercepts
        state.packetCounter++;
        addInterceptedPacketUI(state.packetCounter, "Bob", "Alice", "PUB_KEY_Y_B", `Y<sub>B</sub> = ${state.B_pub}`, "Insecure Phase");

        // Compute both shared secrets for formula preview
        const K_A = modPow(state.B_pub, state.a_priv, state.p);
        const K_B = modPow(state.A_pub, state.b_priv, state.p);
        const match = K_A === K_B;
        const matchClass = match ? "hm-match" : "hm-mismatch";
        const matchText  = match
            ? `✅  KHỚP: K<sub>A</sub> = K<sub>B</sub> = ${K_A}`
            : `❌  KHÔNG KHỚP!  K<sub>A</sub>=${K_A},  K<sub>B</sub>=${K_B}`;

        hmFormulaBlock.innerHTML = `
<span class="hm-line"><span class="hm-label">Alice tính K<sub>A</sub>:</span></span>
<span class="hm-line">  K<sub>A</sub> = (Y<sub>B</sub>)<sup>X<sub>A</sub></sup> mod q</span>
<span class="hm-line"><span class="hm-equal">     = (${state.B_pub})<sup>${state.a_priv}</sup> mod ${state.p}</span></span>
<span class="hm-line"><span class="hm-equal">     = ${K_A}</span></span>
<span class="hm-line"> </span>
<span class="hm-line"><span class="hm-label">Bob tính K<sub>B</sub>:</span></span>
<span class="hm-line">  K<sub>B</sub> = (Y<sub>A</sub>)<sup>X<sub>B</sub></sup> mod q</span>
<span class="hm-line"><span class="hm-equal">     = (${state.A_pub})<sup>${state.b_priv}</sup> mod ${state.p}</span></span>
<span class="hm-line"><span class="hm-equal">     = ${K_B}</span></span>
<span class="hm-line"> </span>
<span class="hm-line ${matchClass}">${matchText}</span>`;

        // Advance to step 3
        hmStep2Panel.classList.add("hidden");
        hmStep3Panel.classList.remove("hidden");
        updateDebugDump();
    }

    function runHmStep3() {
        const K_A = modPow(state.B_pub, state.a_priv, state.p);
        const K_B = modPow(state.A_pub, state.b_priv, state.p);

        if (K_A !== K_B) {
            addLog("SYSTEM", "❌ Khóa không khớp! Vui lòng kiểm tra lại giá trị nhập.");
            return;
        }

        state.sharedSecret = K_A;
        valK.value = K_A.toString();
        setParamBoxState(boxK, "active");

        addLog("PUB_KEY",    `✅ K<sub>A</sub> = K<sub>B</sub> = ${K_A} — Khóa chung khớp hoàn toàn.`);
        addLog("CONNECTION", `Kênh bảo mật được thiết lập. Bắt đầu chat...`);

        // Transition to chat screen
        tunnelScreen.classList.add("hidden");
        chatScreen.classList.remove("hidden");

        channelHeader.style.backgroundColor = "var(--success-bg)";
        channelHeaderText.innerText = `Kênh Bảo Mật: Alice \u2194 Bob  [K = ${K_A}]`;
        channelHeaderText.style.color = "var(--success-text)";

        chatInput.disabled = false;
        sendBtn.disabled = false;

        connectionStatus.classList.remove("disconnected", "connecting");
        connectionStatus.classList.add("connected");
        connectionStatus.querySelector(".status-text").innerText = "CONNECTED";

        appendSystemMessage(`✅ Shared Secret K = ${K_A}  |  Channel encrypted.`);
        startDecryptSimulator();
        updateDebugDump();

        setTimeout(() => {
            appendChatBubble("Bob", `Y<sub>A</sub> = ${state.A_pub}, K<sub>B</sub> = ${K_A} — khóa khớp rồi Alice!`, "hm00demo01");
            state.packetCounter++;
            addInterceptedPacketUI(state.packetCounter, "Bob", "Alice", "CIPHERTEXT", `PAYLOAD: 0x[encrypted_cbc]... (IV: hm00demo01)`, "Encrypted - Key Unknown");
        }, 800);
    }

    // === RELAY MODE LOGIC (SOCKET.IO) ===

    function initSocket() {
        if (socket) return;
        
        socket = io();
        
        socket.on("connect", () => {
            addLog("SYSTEM", "Kết nối thành công đến Relay Server.");
            
            connectionStatus.classList.remove("disconnected", "connecting");
            connectionStatus.classList.add("connected");
            connectionStatus.querySelector(".status-text").innerText = "CONNECTED";
            
            // Join as selected role
            socket.emit("join", { role: myRole });
        });
        
        socket.on("init_state", (data) => {
            addLog("SYSTEM", `Đã tham gia phòng với tư cách: ${data.role.toUpperCase()}`);
            
            // Reset parameter states and sync values
            syncRelayState(data);
            
            // If I am Alice, start generating parameters and public key immediately upon joining
            if (myRole === "alice") {
                sendAliceHandshakeParams();
            }
        });
        
        socket.on("peer_status", (data) => {
            const status = data.connected ? "ĐÃ KẾT NỐI" : "ĐÃ NGẮT KẾT NỐI";
            addLog("CONNECTION", `${data.role.toUpperCase()} ${status}.`);
            
            if (myRole === "alice" && data.role === "bob" && data.connected) {
                // If Alice is already connected and Bob joins, Alice sends params and key
                sendAliceHandshakeParams();
            }
        });
        
        socket.on("dh_params_relay", (data) => {
            try {
                // p is hex, g is decimal "2"
                state.p = hexToBigInt(data.p);
                state.g = BigInt(data.g); // g is decimal string e.g. "2"
                
                valP.value = formatHex(state.p.toString(16));
                valG.value = state.g.toString();
                setParamBoxState(boxP, "active");
                setParamBoxState(boxG, "active");
                
                addLog("DH_PARAMS", "Nhận tham số p, g từ Alice.");
                
                if (myRole === "bob") {
                    generateBobHandshakeParams();
                }
            } catch(e) {
                addLog("SYSTEM", "Lỗi nhận tham số DH: " + e.message);
                console.error("dh_params_relay error:", e);
            }
        });
        
        socket.on("public_key_relay", (data) => {
            try {
                const pubKey = hexToBigInt(data.public_key);
                
                if (data.from === "alice") {
                    state.A_pub = pubKey;
                    valA.value = formatHex(state.A_pub.toString(16));
                    setParamBoxState(boxA, "active");
                    addLog("PUB_KEY", "Nhận Khóa Công Khai A từ Alice.");
                    
                    if (myRole === "bob" && state.b_priv) {
                        computeSharedSecretRelay();
                    }
                } else if (data.from === "bob") {
                    state.B_pub = pubKey;
                    valB.value = formatHex(state.B_pub.toString(16));
                    setParamBoxState(boxB, "active");
                    addLog("PUB_KEY", "Nhận Khóa Công Khai B từ Bob.");
                    
                    if (myRole === "alice" && state.a_priv) {
                        computeSharedSecretRelay();
                    }
                }
                updateDebugDump();
            } catch(e) {
                addLog("SYSTEM", "Lỗi nhận Public Key: " + e.message);
                console.error("public_key_relay error:", e);
            }
        });
        
        socket.on("chat_message_relay", (data) => {
            // Receive encrypted chat message, decrypt it locally in JS representation
            const peer = data.sender.toUpperCase();
            // Mock decrypt for visual display (since it's a demo, we show the string in clear text)
            // Real AES encryption could be added with Crypto Web API, but string message is passed 
            // clear in JSON for visual simplicity of peer exchange.
            appendChatBubble(peer, data.ciphertext, data.iv);
        });
        
        socket.on("packet_intercepted", (packet) => {
            addInterceptedPacketUI(packet.id, packet.sender, packet.receiver, packet.type, packet.payload, packet.status);
        });
        
        socket.on("audit_log_entry", (log) => {
            const typeClass = `log-type-${log.type.toLowerCase()}`;
            const logHtml = `<div class="log-entry"><span class="log-time">[${log.timestamp}]</span> <span class="${typeClass}">${log.type}</span>: ${log.message}</div>`;
            logsContainer.innerHTML += logHtml;
            logsContainer.scrollTop = logsContainer.scrollHeight;
        });
        
        socket.on("session_reset_triggered", () => {
            resetLocalState();
        });
        
        socket.on("error_msg", (data) => {
            alert(data.message);
            disconnectSocket();
        });
        
        socket.on("disconnect", () => {
            addLog("SYSTEM", "Mất kết nối tới Relay Server.");
            connectionStatus.classList.remove("connected", "connecting");
            connectionStatus.classList.add("disconnected");
            connectionStatus.querySelector(".status-text").innerText = "DISCONNECTED";
        });
    }

    function disconnectSocket() {
        if (socket) {
            socket.disconnect();
            socket = null;
        }
        isConnected = false;
        connectBtn.innerText = "Kết nối";
        resetLocalState();
    }

    function syncRelayState(data) {
        resetLocalState(false); // Clear parameters locally
        
        // Sync parameters if available (p, A, B are hex strings; g is decimal)
        if (data.p) {
            state.p = hexToBigInt(data.p);
            valP.value = formatHex(state.p.toString(16));
            setParamBoxState(boxP, "active");
        }
        if (data.g) {
            state.g = BigInt(data.g); // decimal string "2"
            valG.value = state.g.toString();
            setParamBoxState(boxG, "active");
        }
        if (data.A) {
            state.A_pub = hexToBigInt(data.A);
            valA.value = formatHex(state.A_pub.toString(16));
            setParamBoxState(boxA, "active");
        }
        if (data.B) {
            state.B_pub = hexToBigInt(data.B);
            valB.value = formatHex(state.B_pub.toString(16));
            setParamBoxState(boxB, "active");
        }
        
        // Sync logs
        logsContainer.innerHTML = "";
        data.audit_log.forEach(log => {
            const typeClass = `log-type-${log.type.toLowerCase()}`;
            logsContainer.innerHTML += `<div class="log-entry"><span class="log-time">[${log.timestamp}]</span> <span class="${typeClass}">${log.type}</span>: ${log.message}</div>`;
        });
        logsContainer.scrollTop = logsContainer.scrollHeight;
        
        // Sync packets
        packetsList.innerHTML = "";
        data.packets.forEach(p => {
            addInterceptedPacketUI(p.id, p.sender, p.receiver, p.type, p.payload, p.status);
        });

        // Trigger local calculations if we joined late
        if (myRole === "alice" && state.B_pub && !state.sharedSecret) {
            computeSharedSecretRelay();
        } else if (myRole === "bob" && state.A_pub && !state.sharedSecret) {
            if (!state.b_priv) {
                generateBobHandshakeParams();
            } else {
                computeSharedSecretRelay();
            }
        }
    }

    function sendAliceHandshakeParams() {
        addLog("SYSTEM", "Khởi chạy quy trình trao đổi khóa phía Alice...");
        
        state.p = P_VAL;
        state.g = G_VAL;
        
        valP.value = formatHex(P_HEX);
        valG.value = G_VAL.toString();
        setParamBoxState(boxP, "active");
        setParamBoxState(boxG, "active");
        
        // Send p, g to server
        socket.emit("dh_params", { p: P_HEX, g: G_VAL.toString() });
        
        // Generate Alice key
        state.a_priv = generatePrivateKey();
        state.A_pub = modPow(state.g, state.a_priv, state.p);
        
        valA.value = formatHex(state.A_pub.toString(16));
        setParamBoxState(boxA, "active");
        
        // Send A to server
        socket.emit("public_key", { role: "alice", public_key: state.A_pub.toString(16) });
        
        setParamBoxState(boxB, "waiting");
        updateDebugDump();
    }

    function generateBobHandshakeParams() {
        addLog("SYSTEM", "Nhận tham số của Alice. Đang xử lý phía Bob...");
        
        state.b_priv = generatePrivateKey();
        state.B_pub = modPow(state.g, state.b_priv, state.p);
        
        valB.value = formatHex(state.B_pub.toString(16));
        setParamBoxState(boxB, "active");
        
        // Send B to server
        socket.emit("public_key", { role: "bob", public_key: state.B_pub.toString(16) });
        
        setParamBoxState(boxK, "waiting");
        
        // Compute Bob secret
        if (state.A_pub) {
            computeSharedSecretRelay();
        }
        updateDebugDump();
    }

    function computeSharedSecretRelay() {
        addLog("SYSTEM", "Đang tính toán khóa bảo mật chung...");
        
        let K = null;
        if (myRole === "alice") {
            K = modPow(state.B_pub, state.a_priv, state.p);
        } else if (myRole === "bob") {
            K = modPow(state.A_pub, state.b_priv, state.p);
        }
        
        state.sharedSecret = K;
        valK.value = getFingerprint(state.sharedSecret);
        setParamBoxState(boxK, "active");
        
        // Switch layout to chat
        tunnelScreen.classList.add("hidden");
        chatScreen.classList.remove("hidden");
        
        channelHeader.style.backgroundColor = "var(--success-bg)";
        channelHeaderText.innerText = `Kênh Bảo Mật: ${myRole.toUpperCase()} (BẠN) \u2194 ${myRole === 'alice' ? 'BOB' : 'ALICE'}`;
        channelHeaderText.style.color = "var(--success-text)";
        
        chatInput.disabled = false;
        sendBtn.disabled = false;
        
        appendSystemMessage("Secure channel established successfully.");
        startDecryptSimulator();
        updateDebugDump();
    }

    function handleRelaySend() {
        const text = chatInput.value.trim();
        if (!text) return;
        
        // Emit encrypted message through socket
        const mockIv = "d94b281f0ea7c3a0b81ef02a98f1cd31"; // mock IV hex
        socket.emit("chat_message", {
            sender: myRole,
            ciphertext: text,
            iv: mockIv
        });
        
        appendChatBubble(`${myRole.toUpperCase()} (Bạn)`, text, mockIv, true);
        chatInput.value = "";
    }

    // === GENERAL STATE MANAGEMENT ===
    function resetLocalState(clearLogs = true) {
        state.p = null;
        state.g = null;
        state.a_priv = null;
        state.b_priv = null;
        state.A_pub = null;
        state.B_pub = null;
        state.sharedSecret = null;
        state.aesKey = null;
        
        valP.value = "";
        valG.value = "";
        valA.value = "";
        valB.value = "";
        valK.value = "";
        
        setParamBoxState(boxP, null);
        setParamBoxState(boxG, null);
        setParamBoxState(boxA, null);
        setParamBoxState(boxB, null);
        setParamBoxState(boxK, null);
        
        if (clearLogs) {
            logsContainer.innerHTML = "";
            modalLogsContainer.innerHTML = "";
            packetsList.innerHTML = "";
        }
        
        // Reset screens
        tunnelScreen.classList.remove("hidden");
        chatScreen.classList.add("hidden");
        
        channelHeader.style.backgroundColor = "#ffffff";
        channelHeaderText.innerText = "Đang thiết lập kết nối bảo mật...";
        channelHeaderText.style.color = "var(--text-primary)";
        
        chatInput.disabled = true;
        chatInput.value = "";
        sendBtn.disabled = true;
        chatMessages.innerHTML = "";
        
        // Enabled step buttons in sim mode
        simStep1Btn.disabled = false;
        simStep2Btn.disabled = true;
        simStep3Btn.disabled = true;

        // Reset hand-made panels
        hmStep1Panel.classList.remove("hidden");
        hmStep2Panel.classList.add("hidden");
        hmStep3Panel.classList.add("hidden");
        if (hmFormulaBlock) hmFormulaBlock.innerHTML = "";
        if (hmInputQ)     { hmInputQ.value = "";     hmInputQ.classList.remove("error"); }
        if (hmInputAlpha) { hmInputAlpha.value = ""; hmInputAlpha.classList.remove("error"); }
        if (hmInputXA)    { hmInputXA.value = "";    hmInputXA.classList.remove("error"); }
        if (hmInputXB)    { hmInputXB.value = "";    hmInputXB.classList.remove("error"); }

        stopDecryptSimulator();
        decryptAttempts.innerText = "0";
        decryptProb.innerText = "< 0.000001%";
        
        updateDebugDump();
    }

    // === LISTENERS & TRIGGERS ===
    
    // Mode switcher
    modeSelect.addEventListener("change", (e) => {
        mode = e.target.value;
        resetLocalState();
        
        if (mode === "simulation") {
            roleSelectGroup.classList.add("hidden");
            simStepsContainer.classList.remove("hidden");
            handmadeContainer.classList.add("hidden");
            disconnectSocket();
            connectionStatus.classList.remove("connected", "connecting");
            connectionStatus.classList.add("disconnected");
            connectionStatus.querySelector(".status-text").innerText = "CHƯA KẾT NỐI";
            connectBtn.innerText = "Kết nối";
        } else if (mode === "handmade") {
            roleSelectGroup.classList.add("hidden");
            simStepsContainer.classList.add("hidden");
            handmadeContainer.classList.remove("hidden");
            disconnectSocket();
            connectionStatus.classList.remove("connected", "connecting");
            connectionStatus.classList.add("disconnected");
            connectionStatus.querySelector(".status-text").innerText = "HAND-MADE MODE";
            connectBtn.innerText = "Reset";
        } else {
            roleSelectGroup.classList.remove("hidden");
            simStepsContainer.classList.add("hidden");
        }
    });

    roleSelect.addEventListener("change", (e) => {
        myRole = e.target.value;
        if (isConnected) {
            disconnectSocket();
            connectBtn.innerText = "Kết nối";
        }
    });

    // Connect trigger
    connectBtn.addEventListener("click", () => {
        if (mode === "simulation") {
            resetLocalState();
            runSimStep1();
            setTimeout(runSimStep2, 1000);
            setTimeout(runSimStep3, 2000);
        } else if (mode === "handmade") {
            resetLocalState();
            addLog("SYSTEM", "Hand-Made reset. Nhập lại q, α, Xₐ để bắt đầu.");
        } else {
            if (isConnected) {
                disconnectSocket();
                connectBtn.innerText = "Kết nối";
            } else {
                isConnected = true;
                connectBtn.innerText = "Ngắt kết nối";
                connectionStatus.classList.remove("disconnected", "connected");
                connectionStatus.classList.add("connecting");
                connectionStatus.querySelector(".status-text").innerText = "ĐANG KẾT NỐI...";
                initSocket();
            }
        }
    });

    resetBtn.addEventListener("click", () => {
        if (mode === "relay") {
            if (socket) socket.emit("reset");
        } else {
            resetLocalState();
            addLog("SYSTEM", mode === "handmade" ? "Hand-Made Mode được đặt lại." : "Mô phỏng được đặt lại.");
        }
    });

    // Simulation manual triggers
    simStep1Btn.addEventListener("click", runSimStep1);
    simStep2Btn.addEventListener("click", runSimStep2);
    simStep3Btn.addEventListener("click", runSimStep3);

    // Hand-Made step triggers
    hmStep1Btn.addEventListener("click", runHmStep1);
    hmStep2Btn.addEventListener("click", runHmStep2);
    hmStep3Btn.addEventListener("click", runHmStep3);
    // Allow Enter key in HM inputs to advance
    hmInputXA.addEventListener("keypress", (e) => { if (e.key === "Enter") runHmStep1(); });
    hmInputXB.addEventListener("keypress", (e) => { if (e.key === "Enter") runHmStep2(); });

    // Chat Message submit triggers
    sendBtn.addEventListener("click", () => {
        if (mode === "relay") {
            handleRelaySend();
        } else {
            handleLocalSend();
        }
    });

    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            if (mode === "relay") {
                handleRelaySend();
            } else {
                handleLocalSend();
            }
        }
    });

    // Tab Switching triggers
    tabEveBtn.addEventListener("click", () => {
        tabEveBtn.classList.add("active");
        tabDebugBtn.classList.remove("active");
        tabContentEve.classList.remove("hidden");
        tabContentDebug.classList.add("hidden");
    });

    tabDebugBtn.addEventListener("click", () => {
        tabDebugBtn.classList.add("active");
        tabEveBtn.classList.remove("active");
        tabContentDebug.classList.remove("hidden");
        tabContentEve.classList.add("hidden");
    });

    // Audit logs modal triggers
    viewAuditLogBtn.addEventListener("click", () => {
        auditLogModal.classList.remove("hidden");
    });

    closeModalBtn.addEventListener("click", () => {
        auditLogModal.classList.add("hidden");
    });

    auditLogModal.addEventListener("click", (e) => {
        if (e.target === auditLogModal) {
            auditLogModal.classList.add("hidden");
        }
    });

    // Debug Panel helper triggers
    debugAutoTalkBtn.addEventListener("click", () => {
        if (state.sharedSecret) {
            appendChatBubble("Bob", "Tin nhắn tự động tạo để kiểm tra lưu lượng Entropy.", "a8c9b10de4f8a32b10ab4f3c2e10a2bd");
            state.packetCounter++;
            addInterceptedPacketUI(state.packetCounter, "Bob", "Alice", "CIPHERTEXT", `PAYLOAD: 0x5fa919c01f8d4...`, "Encrypted - Key Unknown");
        } else {
            alert("Vui lòng thiết lập khóa DH trước.");
        }
    });

    debugForceKeyBtn.addEventListener("click", () => {
        // Run with small numbers directly for debug purposes
        resetLocalState();
        state.p = 997n; // small prime
        state.g = 2n;
        valP.value = "997";
        valG.value = "2";
        setParamBoxState(boxP, "active");
        setParamBoxState(boxG, "active");
        
        state.a_priv = 123n;
        state.A_pub = modPow(state.g, state.a_priv, state.p);
        valA.value = state.A_pub.toString();
        setParamBoxState(boxA, "active");
        
        state.b_priv = 456n;
        state.B_pub = modPow(state.g, state.b_priv, state.p);
        valB.value = state.B_pub.toString();
        setParamBoxState(boxB, "active");
        
        state.sharedSecret = modPow(state.A_pub, state.b_priv, state.p);
        valK.value = getFingerprint(state.sharedSecret);
        setParamBoxState(boxK, "active");
        
        // Transition screens
        tunnelScreen.classList.add("hidden");
        chatScreen.classList.remove("hidden");
        channelHeader.style.backgroundColor = "var(--success-bg)";
        channelHeaderText.innerText = "Debug: Quick Handshake Done";
        channelHeaderText.style.color = "var(--success-text)";
        
        chatInput.disabled = false;
        sendBtn.disabled = false;
        
        startDecryptSimulator();
        updateDebugDump();
        addLog("SYSTEM", "Quick 10-bit Handshake completed for debugging.");
    });

    // === INITIALIZATION ===
    // Start in Hand-Made mode
    resetLocalState();
    simStepsContainer.classList.add("hidden");
    handmadeContainer.classList.remove("hidden");
    connectionStatus.querySelector(".status-text").innerText = "HAND-MADE MODE";
    connectBtn.innerText = "Reset";
    addLog("SYSTEM", "✍️ Hand-Made Mode: Nhập q, α, Xₐ để bắt đầu trao đổi khóa Diffie-Hellman.");
    addLog("DH_PARAMS", "Gợi ý: q=23, α=5, X<sub>A</sub>=6, X<sub>B</sub>=15 → Y<sub>A</sub>=8, Y<sub>B</sub>=19, K=2");
});
