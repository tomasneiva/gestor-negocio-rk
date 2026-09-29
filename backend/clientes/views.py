from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm
from .models import Cliente


def lista(request):
    clientes = Cliente.objects.all()
    return render(request, "clientes/lista.html", {"clientes": clientes})


def criar(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente cadastrado com sucesso.")
            return redirect("clientes:lista")
    else:
        form = ClienteForm()
    return render(request, "clientes/form.html", {"form": form, "titulo": "Novo cliente"})


def editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado com sucesso.")
            return redirect("clientes:lista")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "clientes/form.html", {"form": form, "titulo": "Editar cliente", "cliente": cliente})
