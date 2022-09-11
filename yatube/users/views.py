from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm, ResetEmailForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


def password_reset(request):
    succes = 'posts:index'
    restart = 'users/password_reset_form.html'
    if request.method == 'POST':
        form = ResetEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            send_mail(
                'Сброс пароля',
                'Сброс пароля',
                'system@mail.com',
                [email]
            )
            return redirect(succes)
        else:
            return render(request, restart, {'form': form})
    else:
        form = ResetEmailForm()
        return render(request, restart, {'form': form})
