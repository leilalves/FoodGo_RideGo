"""
`ridego.views` — a camada VIEW do padrão MVC, num único arquivo.

Cada tela do app é uma classe que herda de `BaseView` e implementa o
método `build()`. As Views só desenham a interface e encaminham eventos do
usuário para o `RideController` — nunca calculam preço, nunca acessam o
histórico diretamente, nunca decidem regra de negócio sozinhas.

Está dividido em blocos, na ordem em que um bloco depende do anterior:

1. `Theme`      — paleta de cores + componentes visuais reutilizados
2. `BaseView`   — classe abstrata da qual toda tela herda
3. `SplashView`, `HomeView`, `CategoriesView`, `MatchingView`, `RateView`,
   `HistoryView` — uma classe por tela, na ordem do fluxo do app
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

import flet as ft
import flet_map as ftm

from ridego.controller import RideController
from ridego.model import CATEGORIES, QUICK_DESTINATIONS, Destination, Ride, RideCategory
from ridego.services import AddressNotFoundError

class Theme:

    PRIMARY = "#5B21B6"       
    PRIMARY_DARK = "#3B0764"  
    ACCENT = "#06B6D4"   
    SUCCESS = "#10B981"    
    WARNING = "#F59E0B" 
    DANGER = "#EF4444"
    BG = "#F5F3FB"    
    INK = "#1F2937"   
    MUTED = "#6B7280"   

    CATEGORY_COLORS = {
        "economico": ACCENT,
        "comfort": PRIMARY,
        "xl": WARNING,
    }

    OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

    @classmethod
    def color_for_category(cls, category_id: str) -> str:
        return cls.CATEGORY_COLORS.get(category_id, cls.PRIMARY)

    @classmethod
    def build_flet_theme(cls) -> ft.Theme:

        return ft.Theme(
            color_scheme_seed=cls.PRIMARY,
            use_material3=True,
            color_scheme=ft.ColorScheme(primary=cls.PRIMARY, secondary=cls.ACCENT),
            appbar_theme=ft.AppBarTheme(
                bgcolor=ft.Colors.TRANSPARENT,
                elevation=0,
                center_title=False,
                title_text_style=ft.TextStyle(size=20, weight=ft.FontWeight.W_800, color=cls.INK),
            ),
            button_theme=ft.ButtonTheme(
                style=ft.ButtonStyle(
                    bgcolor=cls.PRIMARY,
                    color=ft.Colors.WHITE,
                    padding=ft.Padding(24, 18, 24, 18),
                    shape=ft.RoundedRectangleBorder(radius=16),
                    text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
                    elevation=0,
                )
            ),
            text_button_theme=ft.TextButtonTheme(
                style=ft.ButtonStyle(
                    color=cls.ACCENT,
                    text_style=ft.TextStyle(weight=ft.FontWeight.W_600),
                )
            ),
        )

    @staticmethod
    def soft_card(content: ft.Control, padding: int = 16, radius: int = 20, on_click=None) -> ft.Container:

        return ft.Container(
            padding=padding,
            border_radius=radius,
            bgcolor=ft.Colors.WHITE,
            on_click=on_click,
            shadow=ft.BoxShadow(
                blur_radius=18,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.08, Theme.INK),
                offset=ft.Offset(0, 6),
            ),
            content=content,
        )

    @staticmethod
    def icon_badge(icon, color: str, size: int = 44) -> ft.Container:
        return ft.Container(
            width=size,
            height=size,
            border_radius=size / 2,
            bgcolor=ft.Colors.with_opacity(0.12, color),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(icon, color=color, size=size * 0.55),
        )

    @staticmethod
    def eyebrow(text: str) -> ft.Text:
        return ft.Text(
            text.upper(),
            size=11,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE),
            letter_spacing=1.2,
        )

    @staticmethod
    def latlon(coords: tuple[float, float]) -> ftm.MapLatitudeLongitude:
        return ftm.MapLatitudeLongitude(coords[0], coords[1])

class BaseView(ABC):
    
    route: str = "/"

    def __init__(self, page: ft.Page, controller: RideController) -> None:
        self.page = page
        self.controller = controller

    @abstractmethod
    def build(self) -> ft.View:

        raise NotImplementedError

class SplashView(BaseView):

    SPLASH_DURATION_SECONDS = 3

    def __init__(self, page: ft.Page, controller: RideController) -> None:
        super().__init__(page, controller)
        self._logo_badge: ft.Container | None = None

    def build(self) -> ft.View:
        self._logo_badge = ft.Container(
            width=112,
            height=112,
            border_radius=56,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
            content=ft.Icon(ft.Icons.DIRECTIONS_CAR_FILLED_ROUNDED, color=ft.Colors.WHITE, size=58),
            scale=0.6,
            opacity=0,
            animate_scale=ft.Animation(650, ft.AnimationCurve.EASE_OUT_BACK),
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
        )
        brand_column = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Text("RideGo", size=36, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
                ft.Text(
                    "Sua próxima corrida, a poucos toques",
                    size=13,
                    color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                ),
            ],
        )
        spinner = ft.ProgressRing(width=24, height=24, stroke_width=3, color=ft.Colors.WHITE)

        return ft.View(
            route="/splash",
            bgcolor=Theme.PRIMARY_DARK,
            padding=0,
            controls=[
                ft.Container(
                    expand=True,
                    gradient=ft.LinearGradient(
                        colors=[Theme.PRIMARY_DARK, Theme.PRIMARY],
                        begin=ft.Alignment.TOP_CENTER,
                        end=ft.Alignment.BOTTOM_CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=28,
                        controls=[self._logo_badge, brand_column, spinner],
                    ),
                )
            ],
        )

    async def play_intro_and_wait(self) -> None:
        self.page.update()
        await asyncio.sleep(0.05)
        self._logo_badge.scale = 1
        self._logo_badge.opacity = 1
        self.page.update()
        await asyncio.sleep(self.SPLASH_DURATION_SECONDS)


class HomeView(BaseView):

    route = "/"

    def build(self) -> ft.View:
        geolocator = self.controller.create_geolocator()

        origin_marker = ftm.Marker(
            coordinates=Theme.latlon(self.controller.origin_coords),
            content=ft.Icon(ft.Icons.MY_LOCATION, color=Theme.ACCENT, size=32),
        )
        marker_layer = ftm.MarkerLayer(markers=[origin_marker])
        polyline_layer = ftm.PolylineLayer(polylines=[])

        my_map = ftm.Map(
            expand=True,
            initial_center=Theme.latlon(self.controller.origin_coords),
            initial_zoom=13,
            layers=[
                ftm.TileLayer(
                    url_template=Theme.OSM_TILE_URL,
                    user_agent_package_name="ridego-exercise/1.0",
                ),
                ftm.SimpleAttribution(text="© OpenStreetMap contributors"),
                polyline_layer,
                marker_layer,
            ],
        )

        origin_text = ft.Text(
            f"📍 {self.controller.origin_label}", weight=ft.FontWeight.BOLD, color=Theme.INK
        )
        summary_text = ft.Text(color=Theme.MUTED, size=13)
        request_button = ft.Button(
            "Buscar corrida", icon=ft.Icons.SEARCH, width=400, disabled=True
        )
        async def use_my_location(e: ft.Event[ft.Button]) -> None:
            try:
                coords = await self.controller.use_current_location(geolocator)
                origin_text.value = f"📍 {self.controller.origin_label}"
                origin_marker.coordinates = Theme.latlon(coords)
                await my_map.move_to(destination=Theme.latlon(coords), zoom=14)
            except Exception as ex:
                self.page.show_dialog(ft.SnackBar(ft.Text(f"Não foi possível obter o GPS: {ex}")))
            self.page.update()

        def render_destination(destination: Destination, coords: tuple[float, float]) -> None:
            destination_marker = ftm.Marker(
                coordinates=Theme.latlon(coords),
                content=ft.Icon(ft.Icons.LOCATION_ON, color=Theme.DANGER, size=32),
            )
            marker_layer.markers = [origin_marker, destination_marker]
            polyline_layer.polylines = [
                ftm.PolylineMarker(
                    coordinates=[Theme.latlon(self.controller.origin_coords), Theme.latlon(coords)],
                    color=Theme.PRIMARY,
                    border_stroke_width=4,
                )
            ]
            if destination.is_simulated:
                summary_text.value = (
                    f"🧭 ~{destination.distance_km:.1f} km até {destination.label} "
                    "(sem internet — localização aproximada/simulada)"
                )
            else:
                summary_text.value = (
                    f"🧭 {destination.distance_km:.1f} km até {destination.label} "
                    "(rota em linha reta, simplificada)"
                )
            request_button.disabled = False
            self.page.update()

        def select_quick_destination(destination: Destination) -> None:
            coords = self.controller.select_destination(destination)
            render_destination(destination, coords)
            destinations_row.controls = [build_destination_chip(d) for d in QUICK_DESTINATIONS]
            self.page.update()

        address_field = ft.TextField(
            label="Digite um endereço de destino",
            hint_text="Ex.: Av. Paulista, 1000",
            prefix_icon=ft.Icons.SEARCH,
            filled=True,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=Theme.PRIMARY,
            border_radius=14,
            content_padding=ft.Padding(16, 14, 16, 14),
            text_size=14,
            expand=True,
        )
        calc_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
            icon_color=ft.Colors.WHITE,
            bgcolor=Theme.PRIMARY,
            icon_size=20,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
        )

        async def calculate_from_address(e=None) -> None:
            address = (address_field.value or "").strip()
            if not address:
                self.page.show_dialog(ft.SnackBar(ft.Text("Digite um endereço para calcular a rota.")))
                self.page.update()
                return

            address_field.disabled = True
            calc_button.disabled = True
            calc_button.icon = ft.Icons.HOURGLASS_TOP_ROUNDED
            summary_text.value = f'🔎 Buscando "{address}" no mapa...'
            self.page.update()

            try:
                destination, coords = await self.controller.select_destination_from_address(address)
            except AddressNotFoundError:

                summary_text.value = ""
                self.page.show_dialog(
                    ft.SnackBar(
                        ft.Text(
                            f'Não encontramos "{address}". '
                            "Tente incluir rua, número e cidade."
                        )
                    )
                )
            except Exception as ex:
                summary_text.value = ""
                self.page.show_dialog(ft.SnackBar(ft.Text(f"Não foi possível buscar esse endereço: {ex}")))
            else:
                render_destination(destination, coords)
                destinations_row.controls = [build_destination_chip(d) for d in QUICK_DESTINATIONS]
            finally:
                address_field.disabled = False
                calc_button.disabled = False
                calc_button.icon = ft.Icons.ARROW_FORWARD_ROUNDED
                self.page.update()

        address_field.on_submit = calculate_from_address
        calc_button.on_click = calculate_from_address

        def build_destination_chip(destination: Destination) -> ft.Container:
            is_selected = (
                self.controller.destination is not None
                and self.controller.destination.label == destination.label
            )
            return ft.Container(
                padding=ft.Padding(14, 12, 14, 12),
                border_radius=16,
                bgcolor=Theme.PRIMARY if is_selected else ft.Colors.SURFACE_CONTAINER_HIGHEST,
                shadow=(
                    ft.BoxShadow(
                        blur_radius=12,
                        color=ft.Colors.with_opacity(0.25, Theme.PRIMARY),
                        offset=ft.Offset(0, 4),
                    )
                    if is_selected
                    else None
                ),
                on_click=lambda e, d=destination: select_quick_destination(d),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Text(destination.emoji, size=22),
                        ft.Text(
                            destination.label,
                            size=11,
                            weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.NORMAL,
                            color=ft.Colors.WHITE if is_selected else Theme.INK,
                        ),
                    ],
                ),
            )

        destinations_row = ft.Row(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=[build_destination_chip(d) for d in QUICK_DESTINATIONS],
        )

        async def go_to_categories(e) -> None:
            await self.page.push_route("/categories")

        request_button.on_click = go_to_categories

        appbar = ft.AppBar(
            title=ft.Text("Para onde vamos?", weight=ft.FontWeight.W_800),
            actions=[
                ft.IconButton(
                    ft.Icons.HISTORY,
                    icon_color=Theme.PRIMARY,
                    on_click=lambda e: self.page.navigate("/history"),
                )
            ],
        )
        
        map_card = ft.Container(
            height=260,
            margin=ft.Margin(16, 4, 16, 0),
            border_radius=22,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, Theme.PRIMARY_DARK),
                offset=ft.Offset(0, 8),
            ),
            content=my_map,
        )

        bottom_sheet = ft.Container(
            padding=ft.Padding(20, 22, 20, 20),
            bgcolor=ft.Colors.WHITE,
            border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0),
            shadow=ft.BoxShadow(
                blur_radius=24,
                color=ft.Colors.with_opacity(0.10, Theme.INK),
                offset=ft.Offset(0, -6),
            ),
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        controls=[
                            origin_text,
                            ft.TextButton("Usar GPS", icon=ft.Icons.GPS_FIXED, on_click=use_my_location),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[address_field, calc_button],
                    ),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(expand=True, height=1, bgcolor=ft.Colors.with_opacity(0.08, Theme.INK)),
                            ft.Text("ou destinos rápidos", size=11, color=Theme.MUTED, weight=ft.FontWeight.W_600),
                            ft.Container(expand=True, height=1, bgcolor=ft.Colors.with_opacity(0.08, Theme.INK)),
                        ],
                    ),
                    destinations_row,
                    summary_text,
                    request_button,
                ],
            ),
        )

        return ft.View(
            route=self.route,
            bgcolor=Theme.BG,
            padding=0,
            controls=[
                ft.SafeArea(
                    expand=True,
                    content=ft.Column(
                        expand=True,
                        spacing=0,
                        controls=[
                            ft.Container(padding=ft.Padding(8, 4, 8, 0), content=appbar),
                            map_card,
                            ft.Container(
                                expand=True,
                                content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=[bottom_sheet]),
                            ),
                        ],
                    ),
                )
            ],
        )


class CategoriesView(BaseView):


    route = "/categories"

    def build(self) -> ft.View:
        if self.controller.destination is None:
            return self._build_missing_destination_view()

        cards_column = ft.Column(
            spacing=12, controls=[self._build_category_card(c) for c in CATEGORIES]
        )

        appbar = ft.AppBar(title=ft.Text("Escolha uma categoria", weight=ft.FontWeight.W_800))
        summary_banner = self._build_summary_banner()
        body = ft.Container(padding=16, content=ft.Column(spacing=16, controls=[summary_banner, cards_column]))

        return ft.View(
            route=self.route,
            bgcolor=Theme.BG,
            controls=[ft.SafeArea(expand=True, content=ft.Column(expand=True, controls=[appbar, body]))],
        )

    def _build_missing_destination_view(self) -> ft.View:
        return ft.View(
            route=self.route,
            bgcolor=Theme.BG,
            controls=[
                ft.SafeArea(
                    content=ft.Column(
                        controls=[
                            ft.AppBar(title=ft.Text("Escolha uma categoria", weight=ft.FontWeight.W_800)),
                            ft.Container(
                                padding=24,
                                content=ft.Text("Selecione um destino primeiro.", color=Theme.MUTED),
                            ),
                        ]
                    )
                )
            ],
        )

    def _build_summary_banner(self) -> ft.Container:
        destination = self.controller.destination
        return ft.Container(
            padding=16,
            border_radius=18,
            gradient=ft.LinearGradient(
                colors=[Theme.PRIMARY, Theme.PRIMARY_DARK],
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
            ),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.ROUTE, color=ft.Colors.WHITE, size=20),
                    ft.Text(
                        f"{self.controller.origin_label}  →  {destination.label}  "
                        f"({destination.distance_km:.1f} km)",
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_600,
                        size=13,
                    ),
                ],
            ),
        )

    def _build_category_card(self, category: RideCategory) -> ft.Container:
        price, duration = self.controller.price_for(category)
        color = Theme.color_for_category(category.id)
        return Theme.soft_card(
            padding=14,
            radius=18,
            on_click=lambda e, c=category: self._open_confirmation_dialog(c),
            content=ft.Row(
                spacing=14,
                controls=[
                    ft.Container(
                        width=52,
                        height=52,
                        border_radius=26,
                        bgcolor=ft.Colors.with_opacity(0.14, color),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(category.emoji, size=26),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(category.name, weight=ft.FontWeight.BOLD, size=15, color=Theme.INK),
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.PEOPLE, size=14, color=Theme.MUTED),
                                    ft.Text(f"{category.seats} lugares", size=12, color=Theme.MUTED),
                                    ft.Icon(ft.Icons.SCHEDULE, size=14, color=Theme.MUTED),
                                    ft.Text(f"~{duration:.0f} min", size=12, color=Theme.MUTED),
                                ],
                            ),
                        ],
                    ),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=2,
                        controls=[
                            ft.Text(f"R$ {price:.2f}", weight=ft.FontWeight.W_800, size=17, color=color),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=18, color=Theme.MUTED),
                        ],
                    ),
                ],
            ),
        )

    def _open_confirmation_dialog(self, category: RideCategory) -> None:
        price, duration = self.controller.price_for(category)
        color = Theme.color_for_category(category.id)

        async def confirm_and_navigate(category: RideCategory) -> None:
            self.page.pop_dialog()
            self.page.update()
            self.controller.confirm_category(category.id)
            await self.page.push_route("/matching")

        dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=22),
            title=ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=20,
                        bgcolor=ft.Colors.with_opacity(0.14, color),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(category.emoji, size=18),
                    ),
                    ft.Text(f"Confirmar {category.name}", weight=ft.FontWeight.W_800, size=16),
                ],
            ),
            content=ft.Container(
                width=280,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        self._summary_row("Destino", self.controller.destination.label),
                        self._summary_row("Tempo estimado", f"~{duration:.0f} min"),
                        self._summary_row("Valor estimado", f"R$ {price:.2f}", value_color=color, bold_value=True),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                ft.Button(
                    "Confirmar corrida",
                    icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                    on_click=lambda e, c=category: self.page.run_task(confirm_and_navigate, c),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            actions_padding=ft.Padding(20, 0, 20, 16),
        )
        self.page.show_dialog(dialog)

    @staticmethod
    def _summary_row(label: str, value: str, *, value_color: str = Theme.INK, bold_value: bool = False) -> ft.Row:

        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=12,
            controls=[
                ft.Text(label, color=Theme.MUTED, size=13),
                ft.Text(
                    value,
                    weight=ft.FontWeight.W_800 if bold_value else ft.FontWeight.W_600,
                    size=15 if bold_value else 13,
                    color=value_color,
                    text_align=ft.TextAlign.RIGHT,
                    expand=True,
                ),
            ],
        )


class MatchingView(BaseView):

    route = "/matching"

    def build(self) -> ft.View:
        status_icon = ft.Icon(ft.Icons.SEARCH, size=56, color=ft.Colors.WHITE)
        status_icon_background = ft.Container(
            width=110,
            height=110,
            border_radius=55,
            alignment=ft.Alignment.CENTER,
            gradient=ft.LinearGradient(
                colors=[Theme.PRIMARY, Theme.PRIMARY_DARK],
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
            ),
            shadow=ft.BoxShadow(
                blur_radius=24,
                color=ft.Colors.with_opacity(0.35, Theme.PRIMARY),
                offset=ft.Offset(0, 10),
            ),
            content=status_icon,
        )
        status_title = ft.Text("Procurando motorista...", size=19, weight=ft.FontWeight.W_800, color=Theme.INK)
        status_subtitle = ft.Text("Isso costuma levar poucos segundos.", color=Theme.MUTED, size=13)
        progress_bar = ft.ProgressBar(
            width=320, value=None, color=Theme.PRIMARY,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=8, bar_height=8,
        )
        driver_info = ft.Container(visible=False, content=ft.Column(spacing=6))
        action_button = ft.Button(
            "Finalizar corrida", icon=ft.Icons.CHECK_CIRCLE_ROUNDED, visible=False, width=320
        )

        async def run_simulation() -> None:
            await asyncio.sleep(2.5)

            driver = self.controller.current_driver
            category = self.controller.selected_category
            status_icon.icon = ft.Icons.DIRECTIONS_CAR
            status_title.value = "Motorista a caminho!"
            status_subtitle.value = f"{category.emoji} {category.name}"
            progress_bar.value = 0.25
            driver_info.visible = True
            driver_info.content.controls = [
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.CircleAvatar(
                            content=ft.Text(driver.initial, weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.with_opacity(0.15, Theme.PRIMARY),
                            color=Theme.PRIMARY,
                        ),
                        ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text(driver.name, weight=ft.FontWeight.BOLD, color=Theme.INK),
                                ft.Text(f"{driver.car_model} • Placa {driver.plate}", size=12, color=Theme.MUTED),
                            ],
                        ),
                    ],
                ),
            ]
            self.page.update()
            await asyncio.sleep(2.5)

            status_title.value = "Corrida em andamento 🚗"
            status_subtitle.value = (
                f"Rumo a {self.controller.destination.label} • "
                f"~{self.controller.current_duration:.0f} min • R$ {self.controller.current_price:.2f}"
            )
            for progress_value in (0.45, 0.65, 0.85, 1.0):
                progress_bar.value = progress_value
                self.page.update()
                await asyncio.sleep(1)

            status_icon.icon = ft.Icons.FLAG
            status_icon_background.gradient = ft.LinearGradient(
                colors=[Theme.SUCCESS, "#059669"],
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
            )
            status_title.value = "Você chegou! 🏁"
            status_subtitle.value = f"{self.controller.destination.label}"
            action_button.visible = True
            self.page.update()

        async def finish_and_go_to_rating(e) -> None:
            await self.page.push_route("/rate")

        action_button.on_click = finish_and_go_to_rating

        appbar = ft.AppBar(title=ft.Text("Sua corrida", weight=ft.FontWeight.W_800))
        body = ft.Container(
            padding=24,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[status_icon_background, status_title, status_subtitle, progress_bar,
                          driver_info, action_button],
            ),
        )

        view = ft.View(
            route=self.route,
            bgcolor=Theme.BG,
            controls=[ft.SafeArea(expand=True, content=ft.Column(expand=True, controls=[appbar, body]))],
        )
        self.page.run_task(run_simulation)
        return view


class RateView(BaseView):

    route = "/rate"

    def build(self) -> ft.View:
        rating_state = {"value": 5}
        stars_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=0)
        comment_field = ft.TextField(
            label="Comentário (opcional)",
            multiline=True,
            border_radius=14,
            border_color=ft.Colors.with_opacity(0.2, Theme.PRIMARY),
            focused_border_color=Theme.PRIMARY,
        )

        def render_stars() -> None:
            stars_row.controls = [
                ft.IconButton(
                    ft.Icons.STAR if i <= rating_state["value"] else ft.Icons.STAR_BORDER,
                    icon_color=Theme.WARNING,
                    icon_size=32,
                    width=48,
                    height=48,
                    style=ft.ButtonStyle(padding=0),
                    on_click=lambda e, i=i: set_rating(i),
                )
                for i in range(1, 6)
            ]

        def set_rating(i: int) -> None:
            rating_state["value"] = i
            render_stars()
            self.page.update()

        render_stars()

        async def submit_rating(e) -> None:
            await self.controller.finish_ride(rating_state["value"], comment_field.value or "")
            self.page.show_dialog(ft.SnackBar(ft.Text("✅ Avaliação enviada. Obrigado!")))
            await self.page.push_route("/history")

        driver = self.controller.current_driver
        driver_name = driver.name if driver else "seu motorista"

        appbar = ft.AppBar(title=ft.Text("Avalie a corrida", weight=ft.FontWeight.W_800))
        body = ft.Container(
            padding=24,
            content=ft.Column(
                spacing=18,
                controls=[
                    Theme.soft_card(
                        radius=20,
                        padding=22,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=16,
                            controls=[
                                ft.Container(
                                    width=64,
                                    height=64,
                                    border_radius=32,
                                    bgcolor=ft.Colors.with_opacity(0.12, Theme.PRIMARY),
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text(
                                        driver_name[0], size=26, weight=ft.FontWeight.BOLD, color=Theme.PRIMARY
                                    ),
                                ),
                                ft.Text(
                                    f"Como foi sua corrida com {driver_name}?",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=Theme.INK,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                stars_row,
                            ],
                        ),
                    ),
                    comment_field,
                    ft.Button("Enviar avaliação", icon=ft.Icons.SEND, width=400, on_click=submit_rating),
                ],
            ),
        )
        return ft.View(
            route=self.route,
            bgcolor=Theme.BG,
            controls=[ft.SafeArea(expand=True, content=ft.Column(expand=True, controls=[appbar, body]))],
        )


class HistoryView(BaseView):

    route = "/history"

    def build(self) -> ft.View:
        profile_header = self._build_profile_header()
        rides_section = self._build_rides_section()

        appbar = ft.AppBar(
            title=ft.Text("Perfil e histórico", weight=ft.FontWeight.W_800),
            actions=(
                [
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE_ROUNDED,
                        icon_color=Theme.DANGER,
                        tooltip="Limpar histórico de corridas",
                        on_click=lambda e: self._open_clear_history_dialog(),
                    )
                ]
                if self.controller.history
                else []
            ),
        )
        new_ride_button = ft.Container(
            padding=16,
            content=ft.Button(
                "Pedir nova corrida",
                icon=ft.Icons.ADD,
                width=400,
                on_click=lambda e: self.page.navigate("/"),
            ),
        )
        return ft.View(
            route=self.route,
            bgcolor=Theme.BG,
            controls=[
                ft.SafeArea(
                    expand=True,
                    content=ft.Column(
                        expand=True,
                        controls=[
                            appbar,
                            ft.Container(
                                expand=True,
                                padding=ft.Padding(16, 0, 16, 0),
                                content=ft.Column(
                                    expand=True,
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=16,
                                    controls=[profile_header, rides_section],
                                ),
                            ),
                            new_ride_button,
                        ],
                    ),
                )
            ],
        )

    def _build_profile_header(self) -> ft.Container:
        return ft.Container(
            padding=20,
            border_radius=22,
            gradient=ft.LinearGradient(
                colors=[Theme.PRIMARY, Theme.PRIMARY_DARK],
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
            ),
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(
                        content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        radius=28,
                    ),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Usuário Exercício", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.WHITE),
                            ft.Text(
                                f"{len(self.controller.history)} corridas realizadas",
                                color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                                size=13,
                            ),
                        ],
                    ),
                ]
            ),
        )

    def _build_rides_section(self) -> ft.Control:
        history = self.controller.history
        if not history:
            return Theme.soft_card(
                radius=20,
                padding=30,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.DIRECTIONS_CAR_OUTLINED, size=48, color=Theme.MUTED),
                        ft.Text("Você ainda não fez nenhuma corrida.", color=Theme.MUTED),
                    ],
                ),
            )
        return ft.Column(spacing=12, controls=[self._build_ride_card(ride) for ride in history])

    def _build_ride_card(self, ride: Ride) -> ft.Container:
        accent_color = Theme.color_for_category(self._infer_category_id(ride))
        return Theme.soft_card(
            radius=16,
            padding=14,
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Container(width=4, height=54, border_radius=4, bgcolor=accent_color),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"{ride.category_emoji} {ride.origin_label} → {ride.destination_label}",
                                        weight=ft.FontWeight.BOLD,
                                        size=13,
                                        color=Theme.INK,
                                    ),
                                    ft.Text(f"R$ {ride.price:.2f}", weight=ft.FontWeight.W_800,
                                            color=accent_color),
                                ],
                            ),
                            ft.Text(
                                f"{ride.created_at} • {ride.distance_km:.1f} km • {ride.driver_name}",
                                size=12,
                                color=Theme.MUTED,
                            ),
                            self._build_stars_row(ride.rating),
                        ],
                    ),
                ],
            ),
        )

    @staticmethod
    def _build_stars_row(rating: int) -> ft.Row:
        filled = [ft.Icon(ft.Icons.STAR, size=14, color=Theme.WARNING) for _ in range(rating)]
        empty = [ft.Icon(ft.Icons.STAR_BORDER, size=14, color=Theme.WARNING) for _ in range(5 - rating)]
        return ft.Row(spacing=2, controls=filled + empty)


    def _open_clear_history_dialog(self) -> None:


        async def confirm_and_clear() -> None:
            self.page.pop_dialog()
            self.page.update()
            await self.controller.clear_history()
            refreshed_view = type(self)(self.page, self.controller).build()
            self.page.views[-1] = refreshed_view
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=22),
            title=ft.Text("Limpar histórico?", weight=ft.FontWeight.W_800, size=16),
            content=ft.Text(
                "Todas as corridas salvas serão apagadas permanentemente. Essa ação não pode ser desfeita.",
                color=Theme.MUTED,
                size=13,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                ft.Button(
                    "Limpar histórico",
                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                    style=ft.ButtonStyle(bgcolor=Theme.DANGER),
                    on_click=lambda e: self.page.run_task(confirm_and_clear),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            actions_padding=ft.Padding(20, 0, 20, 16),
        )
        self.page.show_dialog(dialog)

    @staticmethod
    def _infer_category_id(ride: Ride) -> str:
        emoji_to_id = {"🚗": "economico", "🚙": "comfort", "🚐": "xl"}
        return emoji_to_id.get(ride.category_emoji, "")