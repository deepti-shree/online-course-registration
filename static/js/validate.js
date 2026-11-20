document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".validate-form").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      const password = form.querySelector('input[name="password"]');
      if (password && password.value.length < 8) {
        event.preventDefault();
        alert("Password must contain at least 8 characters.");
        password.focus();
      }
    });
  });
});
