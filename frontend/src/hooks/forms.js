export function bindForm(form, submit) {
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button[type=submit]');
    const error = form.querySelector('[data-form-error]');
    error.textContent = '';
    button.disabled = true;
    try {
      await submit(Object.fromEntries(new FormData(form)));
    } catch (failure) {
      error.textContent = failure.message;
    } finally {
      button.disabled = false;
    }
  });
}

export function openSheet(container, markup, submit) {
  container.innerHTML = markup;
  const sheet = container.querySelector('dialog');
  sheet.querySelectorAll('[data-close]').forEach(button => button.onclick = () => sheet.close());
  sheet.addEventListener('close', () => container.replaceChildren());
  bindForm(sheet.querySelector('form'), async fields => {
    await submit(fields);
    if (sheet.isConnected) sheet.close();
  });
  sheet.showModal();
}
