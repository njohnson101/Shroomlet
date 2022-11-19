from tkinter import dialog
import pyglet
clock = pyglet.clock
import math

window = pyglet.window.Window(fullscreen=True)
icon = pyglet.image.load('sick_toad.png')
window.set_icon(icon)
window.set_caption('Skyrim')

def merge(a,b):
    return {**a,**b}

def load_image(image):
    img = pyglet.image.load(image)
    img.anchor_x = img.width//2
    img.anchor_y = img.height//2
    return img

background = pyglet.shapes.Rectangle(
    width = window.width,
    height = window.height,
    x=0,y=0,
    color=(50,50,50)
)
blackout=(window.width-math.floor(4/3*window.height))//2
left_shade = pyglet.shapes.Rectangle(
    width = blackout,
    height = window.height,
    x=0,y=0,
    color=(0,0,0)
)
right_shade = pyglet.shapes.Rectangle(
    width = blackout,
    height = window.height,
    x=window.width-blackout,y=0,
    color=(0,0,0)
)

#dialogue_box_image = load_image("textbox.webp")
dialogue_box_image = load_image("obama.png")
dialogue_box = pyglet.sprite.Sprite(dialogue_box_image,x=window.width//2,y=window.height*0.825)
dialogue_box.scale_x = 1.65
dialogue_text = pyglet.text.Label(
    "",
    color=(0,0,0,255),
    anchor_x="center",anchor_y="center",
    x=dialogue_box.x,y=dialogue_box.y,
    width=dialogue_box.width-10,height=dialogue_box.height-10,
    align="center",
    multiline=True,
    font_size = 40
)

class dialogue():
    
    box = dialogue_box
    textbox = dialogue_text
    
    queue = []
    char = 0
    time = 0.0
    speaking = False
    standby = False

    def open_dialogue_box():
        dialogue.box.visible = True

    def close_dialogue_box():
        dialogue.box.visible = False

    def clear():
        dialogue.queue = []
        dialogue.box.visible = False
        dialogue.textbox.text = ""
        dialogue.char = 0

    def update_dialogue(dt):
        dialogue.time += dt
        if not dialogue.standby and dialogue.speaking and dialogue.char<(dialogue.queue[0]["speed"]**-1)*(dialogue.time+dt):
            dialogue.char += 1
            dialogue.textbox.text = dialogue.queue[0]["text"][0:dialogue.char]
            dialogue.textbox.color = dialogue.queue[0]["color"]
            if dialogue.char == len(dialogue.queue[0]["text"]):
                print("standby")
                dialogue.speaking = False
                dialogue.standby = True
        elif dialogue.standby and :


    def speak(text,style):
        dict = merge({"text": text, "length":len(text)},style)
        if not "speed" in dict:
            dict["speed"] = 1/30.0
        dialogue.queue.append(dict)
        if not dialogue.standby:
            dialogue.speaking = True

dialogue.close_dialogue_box()
dialogue.open_dialogue_box()

@window.event
def on_draw():
    window.clear()
    background.draw()
    left_shade.draw()
    right_shade.draw()
    dialogue_box.draw()
    dialogue_text.draw()

pyglet.clock.schedule_interval(dialogue.update_dialogue,1/120.0)

cassy = {
    "font": "Times New Roman",
    "sound": None,
    "color": (0,0,0,255),
    "speed": 1/30.0
}

def on_mouse_press()


dialogue.speak("Le Lorem Ipsum est simplement du faux texte employé dans la composition et la mise en page avant impression.",cassy)

pyglet.app.run()