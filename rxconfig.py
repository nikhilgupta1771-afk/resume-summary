import reflex as rx

config = rx.Config(
    app_name="reflex_resume_copilot",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)