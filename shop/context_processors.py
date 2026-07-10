def cart_context(request):
    """
    Контекст процесор для передачі інформації про кошик у всі шаблони.
    Кошик зберігається в сесії Django.
    """
    cart = request.session.get('cart', {})
    cart_count = sum(item.get('quantity', 0) for item in cart.values())
    return {
        'cart_count': cart_count,
    }
