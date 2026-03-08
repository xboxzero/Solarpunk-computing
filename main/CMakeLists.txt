idf_component_register(
    SRCS
        "main.cpp"
        "web/webserver.cpp"
        "web/captive.cpp"
        "mesh/mesh.cpp"
        "mesh/discovery.cpp"
        "power/solar.cpp"
        "power/sleep.cpp"
        "scripting/engine.cpp"
        "hal/uart.cpp"
        "hal/gpio.cpp"
    INCLUDE_DIRS "."
    EMBED_FILES
        "web/static/index.html"
        "web/static/style.css"
        "web/static/app.js"
)
