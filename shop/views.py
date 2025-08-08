from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Course, CartItem, Category, AffiliateLink, AffiliateSale, Module, Lesson, UserLessonProgress, UserProfile, Enrollment, Purchase, Comment
from decimal import Decimal
import hashlib
from django.utils import timezone
from .forms import ResourceUploadForm, CommentForm
from django.db import models
from shop.models import UserProfile


def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return render(request, 'register.html')
        user = User.objects.create_user(username, email, password)
        user.save()
        code = hashlib.md5(user.username.encode()).hexdigest()[:10]
        AffiliateLink.objects.create(user=user, code=code)
        login(request, user)
        messages.success(request, 'Registro exitoso')
        return redirect('shop:index')
    return render(request, 'register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Inicio de sesión exitoso')
            return redirect('shop:index')
        messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'login.html')

@login_required(login_url='shop:user_login')
def user_logout(request):
    logout(request)
    messages.success(request, 'Sesión cerrada')
    return redirect('shop:index')

@login_required(login_url='shop:user_login')
def courses(request):
    category_id = request.GET.get('category')
    courses = Course.objects.all()
    if category_id:
        courses = courses.filter(category_id=category_id)
    categories = Category.objects.all()
    return render(request, 'courses.html', {'courses': courses, 'categories': categories})

@login_required(login_url='shop:user_login')
def upload_course(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        image = request.FILES.get('image')
        duration = request.POST.get('duration', '')
        level = request.POST.get('level', '')
        category_id = request.POST.get('category')
        affiliate_commission = request.POST.get('affiliate_commission', 10)
        course = Course(
            name=name,
            description=description,
            price=price,
            image=image,
            created_by=request.user,
            duration=duration,
            level=level,
            category_id=category_id,
            affiliate_commission=affiliate_commission
        )
        course.save()
        messages.success(request, 'Curso subido')
        return redirect('shop:courses')
    categories = Category.objects.all()
    return render(request, 'upload.html', {'categories': categories})

@login_required(login_url='shop:user_login')
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.course.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

@login_required(login_url='shop:user_login')
def add_to_cart(request, course_id):
    course = Course.objects.get(id=course_id)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        course=course
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, 'Curso añadido al carrito')
    return redirect('shop:cart')

@login_required(login_url='shop:user_login')
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        messages.warning(request, 'El carrito está vacío')
        return redirect('shop:cart')

    # Calcular total y preparar datos para la plantilla
    total = sum(item.course.price * item.quantity for item in cart_items)
    purchase_data = []
    for item in cart_items:
        # Registrar la compra
        purchase = Purchase.objects.create(
            user=request.user,
            course=item.course,
            quantity=item.quantity,
            total_amount=item.course.price * item.quantity,
            status='Completada'
        )
        # Inscribir al usuario en el curso
        Enrollment.objects.get_or_create(user=request.user, course=item.course)
        purchase_data.append({
            'course': item.course,
            'quantity': item.quantity,
            'total': item.course.price * item.quantity
        })

    # Procesar comisiones de afiliados
    affiliate_code = request.session.get('affiliate_code')
    if affiliate_code:
        try:
            affiliate_link = AffiliateLink.objects.get(code=affiliate_code)
            for item in cart_items:
                commission_percentage = item.course.affiliate_commission / 100
                commission = item.course.price * item.quantity * Decimal(commission_percentage)
                AffiliateSale.objects.create(
                    affiliate_link=affiliate_link,
                    course=item.course,
                    amount=commission
                )
                # Añadir puntos al afiliado
                profile = UserProfile.objects.get_or_create(user=affiliate_link.user)[0]
                profile.points += 10  # 10 puntos por venta
                profile.save()
        except AffiliateLink.DoesNotExist:
            pass

    # Limpiar carrito y sesión
    cart_items.delete()
    if 'affiliate_code' in request.session:
        del request.session['affiliate_code']

    # Mostrar página de checkout con detalles
    context = {
        'purchase_data': purchase_data,
        'total': total,
        'purchased_at': timezone.now()
    }
    messages.success(request, 'Compra realizada con éxito')
    return render(request, 'checkout.html', context)

@login_required(login_url='shop:user_login')
def purchases(request):
    purchases = Purchase.objects.filter(user=request.user).order_by('-purchased_at')
    context = {
        'purchases': purchases
    }
    return render(request, 'purchases.html', context)

def affiliate_redirect(request, code):
    # Lógica existente
    affiliate_link = AffiliateLink.objects.get(code=code)
    affiliate_link.clicks += 1
    affiliate_link.save()
    # Ejemplo de creación de venta (ajusta según tu código)
    course = Course.objects.get(id=some_course_id)
    commission = 10.00  # Ajusta según tu lógica
    sale = AffiliateSale.objects.create(affiliate_link=affiliate_link, course=course, amount=commission)
    # Añadir puntos
    profile = UserProfile.objects.get_or_create(user=affiliate_link.user)[0]
    profile.points += 10  # 10 puntos por venta
    profile.save()
    # Resto de la lógica
    return redirect('shop:course_detail', course_id=course.id)


@login_required
def affiliate_dashboard(request):
    user = request.user
    affiliate_link = AffiliateLink.objects.filter(user=user).first()
    affiliate_sales = AffiliateSale.objects.filter(affiliate_link=affiliate_link) if affiliate_link else []
    total_sales = len(affiliate_sales)
    total_commission = sum(sale.amount for sale in affiliate_sales) if affiliate_sales else 0
    total_clicks = affiliate_link.clicks if affiliate_link else 0
    profile = UserProfile.objects.get_or_create(user=user)[0]  # Añadir
    context = {
        'affiliate_link': affiliate_link,
        'total_clicks': total_clicks,
        'total_sales': total_sales,
        'total_commission': total_commission,
        'affiliate_sales': affiliate_sales,
        'points': profile.points,  # Añadir
    }
    return render(request, 'affiliate_dashboard.html', context)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    has_purchased = False
    progress = 0
    lesson_progress = {}
    total_lessons = 0
    completed_lessons = 0
    first_uncompleted_lesson = None

    if request.user.is_authenticated:
        has_purchased = course.purchases.filter(user=request.user).exists()
        if has_purchased:
            modules = Module.objects.filter(course=course)
            lessons = Lesson.objects.filter(module__course=course)
            total_lessons = lessons.count()
            lesson_progress = {lp.lesson.id: lp.completed for lp in UserLessonProgress.objects.filter(user=request.user, lesson__module__course=course)}
            completed_lessons = sum(1 for lp in lesson_progress.values() if lp)
            progress = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            # Encontrar la primera lección no completada
            for lesson in lessons:
                if not lesson_progress.get(lesson.id, False):
                    first_uncompleted_lesson = lesson
                    break

    # Manejar comentarios
    comments = course.comments.all()
    comment_form = None
    if has_purchased and request.user.is_authenticated:
        if request.method == 'POST':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.course = course
                comment.user = request.user
                comment.save()
                return redirect('shop:course_detail', course_id=course.id)
        else:
            comment_form = CommentForm()

    context = {
        'course': course,
        'has_purchased': has_purchased,
        'progress': progress,
        'lesson_progress': lesson_progress,
        'modules': Module.objects.filter(course=course),
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'first_uncompleted_lesson': first_uncompleted_lesson,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'course_detail.html', context)

@login_required(login_url='shop:user_login')
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    has_purchased = CartItem.objects.filter(user=request.user, course=course).exists()
    if not has_purchased:
        messages.warning(request, 'Debes comprar el curso para acceder a esta lección.')
        return redirect('shop:course_detail', course_id=course.id)
    progress, created = UserLessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'completed': False}
    )
    if request.method == 'POST':
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save()
        messages.success(request, '¡Lección completada!')
        return redirect('shop:course_detail', course_id=course.id)
    return render(request, 'lesson_detail.html', {
        'lesson': lesson,
        'course': course,
        'progress': progress,
    })

@login_required
def upload_resource(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not request.user.groups.filter(name='Creators').exists():
        return redirect('shop:index')
    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.lesson = lesson
            resource.save()
            return redirect('shop:lesson_detail', lesson_id=lesson.id)
    else:
        form = ResourceUploadForm(initial={'lesson': lesson})
    return render(request, 'shop/upload_resource.html', {'form': form, 'lesson': lesson})

@login_required
def instructor_dashboard(request):
    user = request.user
    # Obtener cursos creados por el instructor
    courses = Course.objects.filter(created_by=user)
    # Calcular estudiantes inscritos e ingresos por curso
    course_data = []
    total_income = 0
    total_students = 0
    for course in courses:
        students = Enrollment.objects.filter(course=course).count()
        income = AffiliateSale.objects.filter(course=course).aggregate(total=models.Sum('amount'))['total'] or 0
        total_income += income
        total_students += students
        course_data.append({
            'course': course,
            'students': students,
            'income': income
        })
    context = {
        'course_data': course_data,
        'total_income': total_income,
        'total_students': total_students
    }
    return render(request, 'instructor_dashboard.html', context)