export function poll(action, active, interval = 900) {
  setTimeout(async () => {
    if (!active()) return;
    try {
      if (await action() && active()) poll(action, active, interval);
    } catch (error) {
      const notice = document.querySelector('[data-poll-error]');
      if (notice && active()) notice.textContent = `${error.message} 可用页面上的刷新按钮重试。`;
    }
  }, interval);
}
