document.addEventListener("DOMContentLoaded", function () {
    var campoCep = document.getElementById("id_cep");
    if (!campoCep) return;

    function preencher(id, valor) {
        var campo = document.getElementById(id);
        if (campo && !campo.value && valor) {
            campo.value = valor;
        }
    }

    campoCep.addEventListener("blur", function () {
        var cep = campoCep.value.replace(/\D/g, "");
        if (cep.length !== 8) return;

        fetch("https://viacep.com.br/ws/" + cep + "/json/")
            .then(function (resp) { return resp.json(); })
            .then(function (dados) {
                if (dados.erro) return;
                preencher("id_logradouro", dados.logradouro);
                preencher("id_bairro", dados.bairro);
                preencher("id_cidade", dados.localidade);
                preencher("id_uf", dados.uf);
            })
            .catch(function () {});
    });
});
