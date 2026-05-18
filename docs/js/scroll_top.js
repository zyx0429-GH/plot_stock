
    // ===== Scroll to Top Button =====
    const scrollBtn = document.createElement('div');
    scrollBtn.id = 'scrollTopBtn';
    scrollBtn.innerHTML = '⬆️';
    scrollBtn.style.cssText = 'position: fixed; bottom: 30px; right: 30px; width: 50px; height: 50px; background: #334155; color: #e2e8f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 20px; z-index: 1000; opacity: 0; transition: opacity 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.3);';
    scrollBtn.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });
    document.body.appendChild(scrollBtn);
    
    window.addEventListener('scroll', () => {
        scrollBtn.style.opacity = window.scrollY > 500 ? '1' : '0';
    });
