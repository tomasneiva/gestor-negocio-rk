document.addEventListener("DOMContentLoaded", function () {
    var corpoItens = document.getElementById("corpo-itens");
    var botaoAdd = document.getElementById("botao-add-item");
    var totalForms = document.querySelector('input[name$="-TOTAL_FORMS"]');
    var linhaModelo = document.getElementById("linha-modelo");

    if (botaoAdd && corpoItens && totalForms && linhaModelo) {
        botaoAdd.addEventListener("click", function () {
            var index = parseInt(totalForms.value, 10);
            var html = linhaModelo.innerHTML.split("__prefix__").join(index);
            corpoItens.insertAdjacentHTML("beforeend", html);
            totalForms.value = index + 1;
        });
    }

    document.body.addEventListener("change", function (evento) {
        if (!evento.target.classList.contains("peca-select")) {
            return;
        }
        var select = evento.target;
        var opcao = select.options[select.selectedIndex];
        var preco = opcao ? opcao.getAttribute("data-preco") : null;
        var linha = select.closest(".linha-item");
        if (!preco || !linha) {
            return;
        }
        var campoPreco = linha.querySelector(".campo-preco");
        if (campoPreco && !campoPreco.value) {
            campoPreco.value = preco.replace(".", ",");
        }
    });
});
