from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,HttpResponseForbidden,JsonResponse
from django.contrib import messages,auth
from django.contrib.auth.models import User
from .forms import UserCreationForm
import json
from newsApp import models, forms
from .models import Category, Post



def context_data():
    context = {
        'site_name': 'Simple News Portal',
        'page' : 'home',
        'page_title' : 'News Portal',
        'categories' : models.Category.objects.filter(status = 1).all(),
    }
    return context

# Create your views here.
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Inscription réussie.")
            return redirect('login-page')  # Redirige vers la page de connexion après inscription réussie
        else:
            messages.error(request, "Inscription non réussie. Informations invalides.")
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def home(request):
    # Récupérer uniquement les posts approuvés et publiés
    approved_posts = Post.objects.filter(status='approved', is_published=True)
    
    # Récupérer toutes les catégories
    categories = Category.objects.all()

    # Passer les posts et les catégories à votre template
    context = {'approved_posts': approved_posts, 'categories': categories}

    return render(request, 'home.html', context)


#login
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
            else:
                resp['msg'] = "Incorrect username or password"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp),content_type='application/json')

#Logout
def logoutuser(request):
    logout(request)
    return redirect('/')


@login_required
def update_profile(request):
    context = context_data()
    context['page_title'] = 'Update Profile'
    user = User.objects.get(id = request.user.id)
    if not request.method == 'POST':
        form = forms.UpdateProfile(instance=user)
        context['form'] = form
        print(form)
    else:
        form = forms.UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated")
            return redirect("profile-page")
        else:
            context['form'] = form
            
    return render(request, 'update_profile.html',context)

@login_required
def pending_posts(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à cette page.")
    
    # Récupérer toutes les publications en attente de validation
    pending_posts = Post.objects.filter(status='pending')
    
    return render(request, 'pending_posts.html', {'pending_posts': pending_posts})  
@login_required
def update_password(request):
    context = context_data()
    context['page_title'] = "Update Password"
    if request.method == 'POST':
        form = forms.UpdatePasswords(user = request.user, data= request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile-page")
        else:
            context['form'] = form
    else:
        form = forms.UpdatePasswords(request.POST)
        context['form'] = form
    return render(request,'update_password.html',context)

@login_required
def profile(request):
    context = context_data()
    context['page'] = 'profile'
    context['page_title'] = "Profile"
    return render(request,'profile.html', context)

@login_required
def manage_post(request, pk = None):
    context = context_data()
    if not pk is None:
        context['page']='edit_post'
        context['page_title']='Edit Post'
        context['post']=models.Post.objects.get(id=pk)
    else:
        context['page']='new_post'
        context['page_title']='New Post'
        context['post']={}

    return render(request, 'manage_post.html',context)

@login_required
def save_post(request):
    resp = {'status': 'failed', 'msg': '', 'id': None}
    if request.method == 'POST':
        form = forms.savePost(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.status = 'pending'  # Définir le statut du post comme "en attente de validation"
            post.save()
            resp['id'] = post.id
            resp['status'] = 'success'
            messages.success(request, "La publication a été enregistrée avec succès et est en attente de validation par l'administrateur.")
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += '<br />'
                    resp['msg'] += f"[{field.label}] {error}"
    else:
        resp['msg'] = "La requête ne contient aucune donnée."
    return JsonResponse(resp)



def view_post(request, pk=None):
    context = context_data()
    post = models.Post.objects.get(id = pk)
    context['page'] = 'post'
    context['page_title'] = post.title
    context['post'] = post
    context['latest'] = models.Post.objects.exclude(id=pk).filter(status = 1).order_by('-date_created').all()[:10]
    context['comments'] = models.Comment.objects.filter(post=post).all()
    context['actions'] = False
    if request.user.is_superuser or request.user.id == post.user.id:
        context['actions'] = True
    return render(request, 'single_post.html', context)

def save_comment(request):
    resp = {'status': 'failed', 'msg': '', 'id': None}
    if request.method == 'POST':
        # Si l'utilisateur est connecté, ne pas rendre les champs 'name' et 'email' obligatoires
        if request.user.is_authenticated:
            form = forms.saveComment(request.POST, initial={'name': request.user.username, 'email': request.user.email})
        else:
            form = forms.saveComment(request.POST)

        if form.is_valid():
            form.save()
            if request.POST['id'] == '':
                commentID = models.Post.objects.all().last().id
            else:
                commentID = request.POST['id']
            resp['id'] = commentID
            resp['status'] = 'success'
            messages.success(request, "Comment has been saved successfully.")
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str('<br />')
                    resp['msg'] += str(f"[{field.label}] {error}")
    else:
        resp['msg'] = "Request has no data sent."
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def list_posts(request):
    context = context_data()
    context['page'] = 'all_post'
    context['page_title'] = 'All Posts'
    if request.user.is_superuser:
        context['posts'] = models.Post.objects.order_by('-date_created').all()
    else:
        context['posts'] = models.Post.objects.filter(user=request.user).all()

    context['latest'] = models.Post.objects.filter(status = 1).order_by('-date_created').all()[:10]
    
    return render(request, 'posts.html', context)


def category_posts(request, pk=None):
    context = context_data()
    if pk is None:
        messages.error(request, "File not Found")
        return redirect('home-page')
    try:
        category = models.Category.objects.get(id=pk)
    except:
        messages.error(request, "File not Found")
        return redirect('home-page')

    context['category'] = category
    context['page'] = 'category_post'
    context['page_title'] = f'{category.name} Posts'
    # Récupérer uniquement les posts approuvés et publiés de cette catégorie
    context['posts'] = models.Post.objects.filter(status='approved', is_published=True, category=category).all()

    context['latest'] = models.Post.objects.filter(status='approved', is_published=True).order_by('-date_created').all()[:10]

    return render(request, 'category.html', context)


@login_required
def delete_post(request, pk = None):
    resp = {'status':'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Post ID is Invalid'
        return HttpResponse(json.dumps(resp), content_type="application/json")
    try:
        post = models.Post.objects.get(id=pk)
        post.delete()
        messages.success(request, "Post has been deleted successfully.")
        resp['status'] = 'success'
    except:
        resp['msg'] = 'Post ID is Invalid'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def delete_comment(request, pk = None):
    resp = {'status':'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Comment ID is Invalid'
        return HttpResponse(json.dumps(resp), content_type="application/json")
    try:
        comment = models.Comment.objects.get(id=pk)
        comment.delete()
        messages.success(request, "Comment has been deleted successfully.")
        resp['status'] = 'success'
    except:
        resp['msg'] = 'Comment ID is Invalid'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")

@user_passes_test(lambda u: u.is_superuser)
def manage_posts(request):
    pending_posts = Post.objects.filter(status='pending')

    return render(request, 'manage_posts.html', {'pending_posts': pending_posts})

def approve_post(request, post_id):
    # Récupérer la publication à approuver
    post = Post.objects.get(pk=post_id)
    
    # Vérifier si la demande est une requête POST
    if request.method == 'POST':
        # Approuver la publication en changeant son statut
        post.status = 'approved'
        
        # Publier la publication en changeant son statut à 'published'
        post.is_published = True
        
        # Sauvegarder les modifications
        post.save()
        
        # Rediriger l'utilisateur vers la page d'accueil
        return redirect('home-page')  # Assurez-vous que 'home-page' est l'URL de votre page d'accueil
    
    # Si ce n'est pas une requête POST, simplement rediriger l'utilisateur vers la page d'accueil
    return redirect('home-page')