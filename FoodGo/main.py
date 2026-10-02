import flet as ft

from controller import AppController
from views import (
    BG,
    CartView,
    CheckoutView,
    HomeView,
    OrdersView,
    RestaurantView,
    SplashView,
    build_theme,
)

def _build_view_for_route(page: ft.Page, app: AppController) -> ft.View:

    troute = ft.TemplateRoute(page.route)

    if troute.match("/restaurant/:id"):
        view = RestaurantView(page, app, troute.id)
    elif page.route == "/cart":
        view = CartView(page, app)
    elif page.route == "/checkout":
        view = CheckoutView(page, app)
    elif page.route == "/orders":
        view = OrdersView(page, app)
    else:
        view = HomeView(page, app)

    return view.build()

async def main(page: ft.Page):

    page.title = "FoodGo - exercício de clone de app de delivery"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = build_theme()
    page.bgcolor = BG

    page.window.width = 320
    page.window.height = 600
    page.window.min_width = 320
    page.window.max_width = 320
    page.window.min_height = 600
    page.window.max_height = 600
    page.window_resizable = False
    page.update()
    try:
        await page.window.center()
    except Exception:
        pass

    app_controller = AppController()
    prefs = ft.SharedPreferences()
    page.services.append(prefs)
    app_controller.bind(prefs)
    await app_controller.load()

    def route_change(e=None):
        page.views.clear()
        page.views.append(_build_view_for_route(page, app_controller))
        page.update()

    async def on_view_pop(e: ft.ViewPopEvent):
        if e.view is not None and len(page.views) > 1:
            page.views.remove(e.view)
            await page.push_route(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = on_view_pop

    await SplashView(page, app_controller).show()
    page.route = page.route if page.route not in (None, "/Splash") else "/"
    route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")