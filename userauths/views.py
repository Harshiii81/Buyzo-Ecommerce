from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from core.models import Order, SavedAddress


User = get_user_model()


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect("core:index")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("core:index")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)
        messages.success(request, "Account created successfully!")

        return redirect("core:index")

    return redirect("core:index")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            email=email,
            password=password
        )

        if user is not None:
            login(request, user)
            messages.success(request, "Welcome back!")
            return redirect("core:index")

        messages.error(request, "Invalid email or password.")

    return redirect("core:index")


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect("core:index")

@login_required(login_url="core:index")
def account_view(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    addresses = SavedAddress.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, "userauths/account.html", {
        "orders": orders,
        "addresses": addresses,
    })

@require_POST
@login_required(login_url="core:index")
def cancel_order_view(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    if order.status not in ['pending', 'confirmed']:
        messages.error(
            request,
            "This order can no longer be cancelled."
        )
        return redirect("userauths:account")

    order.status = 'cancelled'
    order.save(update_fields=['status'])

    messages.success(
        request,
        f"Order #{order.id} has been cancelled successfully."
    )

    return redirect("userauths:account")


@require_POST
@login_required(login_url="core:index")
def save_address_view(request):
    full_name = request.POST.get("full_name", "").strip()
    phone = request.POST.get("phone", "").strip()
    house_address = request.POST.get("house_address", "").strip()
    street_address = request.POST.get("street_address", "").strip()
    landmark = request.POST.get("landmark", "").strip()
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()
    pincode = request.POST.get("pincode", "").strip()

    if not all([
        full_name, phone, house_address,
        street_address, city, state, pincode
    ]):
        messages.error(request, "Please fill in all required fields.")
        return redirect("userauths:account")

    if not phone.isdigit() or len(phone) != 10:
        messages.error(request, "Enter a valid 10-digit phone number.")
        return redirect("userauths:account")

    if not pincode.isdigit() or len(pincode) != 6:
        messages.error(request, "Enter a valid 6-digit PIN code.")
        return redirect("userauths:account")

    is_default = (
        request.POST.get("is_default") == "on"
        or not SavedAddress.objects.filter(user=request.user).exists()
    )

    if is_default:
        SavedAddress.objects.filter(user=request.user).update(
            is_default=False
        )

    SavedAddress.objects.create(
        user=request.user,
        full_name=full_name,
        phone=phone,
        house_address=house_address,
        street_address=street_address,
        landmark=landmark,
        city=city,
        state=state,
        pincode=pincode,
        is_default=is_default,
    )

    messages.success(request, "Address saved successfully!")
    return redirect("userauths:account")

@require_POST
@login_required(login_url="core:index")
def update_profile_view(request):
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip().lower()

    if not username or not email:
        messages.error(request, "Username and email are required.")
        return redirect("userauths:account")

    if User.objects.filter(email=email).exclude(
        id=request.user.id
    ).exists():
        messages.error(request, "This email is already registered.")
        return redirect("userauths:account")

    request.user.username = username
    request.user.email = email
    request.user.save()

    messages.success(request, "Profile updated successfully!")
    return redirect("userauths:account")