// ShareHub main script — grows in later phases.
document.addEventListener("DOMContentLoaded", () => {
  // Auto-dismiss flash messages after 5 seconds
  document.querySelectorAll(".alert-dismissible").forEach((el) => {
    setTimeout(() => {
      bootstrap.Alert.getOrCreateInstance(el).close();
    }, 5000);
  });
});
