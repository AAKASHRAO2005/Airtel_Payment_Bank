document.addEventListener("DOMContentLoaded", () => {
    // 1. Dark Mode Toggle
    const themeToggle = document.getElementById("theme-toggle");
    const currentTheme = localStorage.getItem("theme");

    if (currentTheme) {
        document.documentElement.setAttribute("data-theme", currentTheme);
        if (currentTheme === "dark" && themeToggle) {
            themeToggle.checked = true;
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener("change", function () {
            if (this.checked) {
                document.documentElement.setAttribute("data-theme", "dark");
                localStorage.setItem("theme", "dark");
            } else {
                document.documentElement.setAttribute("data-theme", "light");
                localStorage.setItem("theme", "light");
            }
        });
    }

    // 2. Animated Counter for Balance
    const balanceElem = document.getElementById("animated-balance");
    if (balanceElem) {
        fetchBalance(balanceElem);
        // Auto refresh every 10 seconds
        setInterval(() => fetchBalance(balanceElem), 10000);
    }

    // 3. Form Loading Spinner
    const forms = document.querySelectorAll("form");
    const loader = document.getElementById("loader");

    forms.forEach(form => {
        form.addEventListener("submit", () => {
            if (loader && form.checkValidity()) {
                loader.classList.add("active");
            }
        });
    });

    // 4. Play Success Sound on certain pages
    const successElement = document.getElementById("success-anim");
    if (successElement) {
        playSuccessSound();
    }
});

function fetchBalance(element) {
    fetch('/api/get-balance')
        .then(response => response.json())
        .then(data => {
            if (data.balance !== undefined) {
                animateValue(element, parseFloat(element.innerText.replace(/,/g, '')) || 0, data.balance, 1000);
            }
        })
        .catch(err => console.error("Error fetching balance", err));
}

function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        
        // Easing function outQuart
        const easeOut = 1 - Math.pow(1 - progress, 4);
        const current = start + (end - start) * easeOut;
        
        obj.innerHTML = current.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            obj.innerHTML = end.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
    };
    window.requestAnimationFrame(step);
}

function playSuccessSound() {
    // A simple short high-pitched ping using Web Audio API
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
        oscillator.frequency.exponentialRampToValueAtTime(1760, audioCtx.currentTime + 0.1); // A6
        
        gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
        
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.5);
    } catch(e) {
        console.log("Audio not supported or blocked");
    }
}

// Sidebar toggle for mobile
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}
