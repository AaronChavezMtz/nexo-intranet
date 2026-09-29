// Inicializa y muestra los toasts (notificaciones no bloqueantes)
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".toast").forEach(function (toastEl) {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    });
});

// Modal de confirmación reutilizable, reemplaza al confirm() nativo del navegador.
// Uso en un <form>: onsubmit="return confirmAction(this, 'Mensaje a mostrar');"
function confirmAction(form, message) {
    const modalEl = document.getElementById("confirmModal");
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    document.getElementById("confirmModalBody").textContent = message;

    const oldBtn = document.getElementById("confirmModalAcceptBtn");
    const newBtn = oldBtn.cloneNode(true); // evita acumular listeners de usos anteriores
    oldBtn.parentNode.replaceChild(newBtn, oldBtn);

    newBtn.addEventListener("click", function () {
        modal.hide();
        form.submit();
    });

    modal.show();
    return false; // evita el envío inmediato del formulario
}