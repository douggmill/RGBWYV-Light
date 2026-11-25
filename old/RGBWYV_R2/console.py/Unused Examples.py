#####################Tab1 Sliders Absolute Placement#######################
# slider_colors = ["red", "yellow", "green", "blue", "purple", "white", "black"]
# slider_names = ["Red \n(%)", "Amber \n(%)", "Green \n(%)", "Blue \n(%)", "Violet \n(%)", "White \n(%)",
#                 "PWM ƒ \n(x10kHz)"]
# sliders = []
# slider_foreground = "black"
# for i in range(7):  # Place sliders on the canvas
#     if slider_colors[i] == "black":
#         slider_foreground = "white"
#     else:
#         slider_foreground = "black"
#     adc_name = f"adc{42 + i}"  # Naming sliders adc42 to adc48
#     frame = tk.Frame(canvas1, bg="lightblue")  # Create a frame to group slider and label
#     label = tk.Label(frame, text=slider_names[i], font=tab_fonts, bg="lightblue")
#     label.pack()  # Create label for the slider
#     slider = tk.Scale(  # Create slider
#         frame,
#         from_=1.0,
#         to=0.0,
#         resolution=0.01,
#         orient="vertical",
#         length=120,
#         fg=slider_foreground,
#         bg=slider_colors[i % len(slider_colors)],  # Cycle through colors
#         command=lambda value, name=adc_name: send_slider_value(name, float(value))
#         #command = lambda value, name=adc_name: send_linear_value(name, float(value))
#     )
#     slider.pack()
#     sliders.append(slider)  # Store slider in list
#     canvas1.create_window(50 + i * 60, 325, window=frame)


##########Tab1 Canvas Background Fixed Size#############
# image_path = "AdditiveColorMixing.png"  # Load the background image
# original_image = Image.open(image_path)
# resized_image = original_image.resize((400, 400), Image.Resampling.LANCZOS)  # Resize if needed
# bg_image = ImageTk.PhotoImage(resized_image)
# canvas1 = tk.Canvas(tab1, width=400, height=400)  # Create a Canvas and set background image
# canvas1.pack(fill="both", expand=True)
# canvas1.create_image(0, 0, image=bg_image, anchor="nw")  # Place image on canvas
# canvas1.bg_image = bg_image  # Keep a reference to avoid garbage collection

#############Canvas Background Flat Color################
# tab1_background = "lightblue"  # back color option
# canvas1 = tk.Canvas(tab1, bg=tab1_background, width=400, height=400)
# canvas1.pack(fill="both", expand=True)

#####################Tab1 Tooltip#######################
# def update_tooltip1(event):
#     """ Update tooltip position and display coordinates """
#     x, y = event.x, event.y
#     tooltip1.config(text=f"({x}, {y})")  # Update text
#     tooltip1.place(x=x + 10, y=y + 10)  # Offset tooltip slightly
#
#
# def hide_tooltip1(event):
#     """ Hide tooltip when mouse leaves the canvas """
#     tooltip1.place_forget()
#
#
# # Tooltip label for coordinates
# tooltip1 = tk.Label(canvas1, text="", font=tab_fonts, bg="white", relief="solid", bd=1)
# tooltip1.place_forget()  # Initially hidden
# canvas1.bind("<Motion>", update_tooltip1)  # Bind mouse motion to update tooltip
# canvas1.bind("<Leave>", hide_tooltip1)  # Hide tooltip when leaving canvas