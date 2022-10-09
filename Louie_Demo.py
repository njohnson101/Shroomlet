#region Some Stuff----------------------------------------------------------------------------------------------------------------------------------------------
import pyglet
import math
mouse = pyglet.window.mouse
clock = pyglet.clock

hitboxes = pyglet.graphics.Batch()

window = pyglet.window.Window(fullscreen=True)
icon = pyglet.image.load('sick_toad.png')
window.set_icon(icon)
window.set_caption('Skyrim')

def load_image(image):
    img = pyglet.image.load(image)
    img.anchor_x = img.width//2
    img.anchor_y = img.height//2
    return img

def meters(feet, inches=0):
    return (feet + inches/12)*0.3048


physical_objects = []
stage_objects = []
objects = []

#endregion----------------------------------------------------------------------------------------------------------------------------------------------------

#region Generate----------------------------------------------------------------------------------------------------------------------------------------------
import pyglet
key = pyglet.window.key

class vector(object):
    def __init__(self,x,y):
        self.x, self.y = x,y
    def __str__(self):
        return "("+str(self.x)+","+str(self.y)+")"
    def __add__(self, other):
        if other.__class__.__name__ == "vector":
            return vector(self.x + other.x,self.y + other.y)
        else:
            return vector(self.x+other, self.y+other)
    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)
    def __sub__(self, other):
        if other.__class__.__name__ == "vector":
            return vector(self.x - other.x,self.y - other.y)
        else:
            return vector(self.x-other, self.y-other)
    def __mul__(self, other):
        if other.__class__.__name__ == "vector":
            return vector(self.x*other.x, self.y*other.y)
        else:
            return vector(self.x*other, self.y*other)
    def __truediv__(self,other):
        if other.__class__.__name__ == "vector":
            return vector(self.x/other.x, self.y/other.y)
        else:
            return vector(self.x/other, self.y/other)
    def __neg__(self):
        return vector(-self.x, -self.y)
    def __eq__(self, other):
        if other.__class__.__name__ != "vector":
            return False
        else:
            if other.x == self.x and other.y == self.y:
                return True
            else:
                return False
    def __ne__(self,other):
        if other.__class__.name__ != "vector":
            return True
        else:
            if other.x == self.x or other.y == self.y:
                return False
            else:
                return True

class hitbox(pyglet.shapes.Rectangle):
    def __init__(self, scale = vector(1,1), offset = vector(0,0), *args, **kwargs):
        super().__init__(x=0,y=0,width=0,height=0,*args, **kwargs)
        self.opacity = 128
        self.scale = scale #when multiplied by height/width will get size
        self.offset = offset #when multiplied by height/width will get offset
        self.world_pos = vector(0,0)
        self.world_size = vector(0,0)
        self.batch = hitboxes

class world_object(pyglet.sprite.Sprite):
    def __init__(self, world_pos = vector(0,0), world_size=0, zindex=1, supered=False, *args, **kwargs):
        super().__init__(x=0,y=0,*args,**kwargs)
        self.__dict__["world_pos"] = world_pos
        if supered:
            self.__dict__["world_size"] = world_size
        else:
            self.world_size = world_size
        self.tweens = []
        self.zindex = zindex
        objects.append(self)
    def __setattr__(self, key, value):
        if key == "world_size":
            if value.__class__.__name__ != "vector":
                self.__dict__["world_size"] = vector(self.image.width/self.image.height*value, value)
            else:
                self.__dict__["world_size"] = value
        else:
            super().__setattr__(key, value)

class physical_object(world_object):
     
    def __init__(self, hitboxes = None, velocity = vector(0,0), anchored = True, *args, **kwargs):
        super().__init__(supered=True,*args,**kwargs)
        if hitboxes == None:
            self.hitboxes = [hitbox()]
        else:
            self.hitboxes = hitboxes
        for i in self.hitboxes:
            i.color = (0,0,255)
            i.parent = self
        self.world_size = self.world_size
        self.movement_restrictions = dict(left=False, right=False, up=False, down=False)
        self.velocity = velocity
        self.anchored = anchored
        physical_objects.append(self)

    def update_hitboxes(self):
        for i in self.hitboxes:
            i.world_pos = vector(self.world_pos.x + self.world_size.x*i.offset.x, self.world_pos.y + self.world_size.y*i.offset.y)
            i.world_size = vector(self.world_size.x*i.scale.x, self.world_size.y*i.scale.y)

    def __setattr__(self, key, value):
        if key == "world_pos":
            self.__dict__["world_pos"] = value
            self.update_hitboxes()
        elif key == "world_size":
            if value.__class__.__name__ != "vector":
                self.__dict__["world_size"] = vector(self.image.width/self.image.height*value, value)
            else:
                self.__dict__["world_size"] = value
            self.update_hitboxes()
        else:
            super().__setattr__(key, value)

    def update(self,dt):
        if not self.movement_restrictions['down']:
            self.velocity.y += 2*gravitational_acceleration*dt
        x_update, y_update = 0,0
        if self.velocity.x < 0 and not self.movement_restrictions['left']:
            x_update = self.velocity.x * dt
        elif self.velocity.x > 0 and not self.movement_restrictions['right']:
            x_update = self.velocity.x * dt
        if self.velocity.y < 0 and not self.movement_restrictions['down']:
            y_update = self.velocity.y * dt
        elif self.velocity.y > 0 and not self.movement_restrictions['up']:
            y_update = self.velocity.y * dt
        self.world_pos += vector(x_update, y_update)  

class stage(physical_object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        for i in self.hitboxes:
            i.color=(139,69,19)
        stage_objects.append(self)

class player_class(physical_object):
    def __init__(self, speed=10, jump_height=0, life = 100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in self.hitboxes:
            i.color = (0,255,0)
        self.keys = dict(left=False, right=False, space=False)
        self.speed = speed #velocity
        self.jump_height = jump_height
        self.life = life
        self.walking = dict(left=False,right=False)
        self.collisions = []
        self.anchored = False
    
    def on_key_press(self, button, modifiers):
        if button == key.LEFT:
            self.keys['left'] = True
        elif button == key.RIGHT:
            self.keys['right'] = True
        elif button == key.SPACE:
            self.keys['space'] = True

    def on_key_release(self, button, modifiers):
        if button == key.LEFT:
            self.keys['left'] = False
        elif button == key.RIGHT:
            self.keys['right'] = False
        elif button == key.SPACE:
            self.keys['space'] = False

    def check_collisions(self, objs, dt):
        hitboxes = self.hitboxes
        self.collisions = []
        self.movement_restrictions = dict(left=False, right=False, up=False, down=False)
        for i in hitboxes:
            x_lower_1, x_upper_1 = i.world_pos.x - i.world_size.x/2, i.world_pos.x + i.world_size.x/2
            y_lower_1, y_upper_1 = i.world_pos.y - i.world_size.y/2, i.world_pos.y + i.world_size.y/2
            for m in objs:
                for w in m.hitboxes:
                    # 2 rectangles
                    if isinstance(w, hitbox):
                        x_lower_2, x_upper_2 = w.world_pos.x - w.world_size.x/2, w.world_pos.x + w.world_size.x/2
                        y_lower_2, y_upper_2 = w.world_pos.y - w.world_size.y/2, w.world_pos.y + w.world_size.y/2
                        x_lower_2_colliding = x_lower_2>=x_lower_1 and x_lower_2<=x_upper_1
                        x_lower_1_colliding = x_lower_1>=x_lower_2 and x_lower_1<=x_upper_2
                        y_lower_2_colliding = y_lower_2>=y_lower_1 and y_lower_2<=y_upper_1
                        y_lower_1_colliding = y_lower_1>=y_lower_2 and y_lower_1<=y_upper_2
                        if (x_lower_2_colliding or x_lower_1_colliding) and (y_lower_2_colliding or y_lower_1_colliding):
                            self.collisions.append(i)
                            if m.__class__.__name__ == "stage":
                                x_overlap = None
                                y_overlap = None
                                if x_lower_2_colliding and not x_lower_1_colliding:
                                    x_overlap = abs(x_lower_2-x_upper_1)
                                elif x_lower_1_colliding and not x_lower_2_colliding:
                                    x_overlap = abs(x_lower_1-x_upper_2)
                                else:
                                    # x_lower_2_colliding and x_lower_1_colliding
                                    if i.world_size.x < w.world_size.x:
                                        x_overlap = i.world_size.x
                                    else:
                                        x_overlap = w.world_size.x
                                if y_lower_2_colliding and not y_lower_1_colliding:
                                    y_overlap = abs(y_lower_2-y_upper_1)
                                elif y_lower_1_colliding and not y_lower_2_colliding:
                                    y_overlap = abs(y_lower_1-y_upper_2)
                                else:
                                    # y_lower_2_colliding and y_lower_1_colliding
                                    if i.world_size.y < w.world_size.y:
                                        y_overlap = i.world_size.y
                                    else:
                                        y_overlap = w.world_size.y
                                if y_overlap > x_overlap:
                                    if x_lower_2_colliding and not x_lower_1_colliding:
                                        self.movement_restrictions['right'] = True
                                        self.world_pos -= vector(x_overlap,0)
                                    elif x_lower_1_colliding and not x_lower_2_colliding:
                                        self.movement_restrictions['left'] = True
                                        self.world_pos += vector(x_overlap,0)
                                    else:
                                        if i.x < w.x:
                                            self.movement_restrictions['right'] = True
                                            self.world_pos -= vector(x_overlap,0)
                                        else:
                                            self.movement_restrictions['left'] = True
                                            self.world_pos += vector(x_overlap,0,)
                                else:
                                    if y_lower_1_colliding and not y_lower_2_colliding:
                                        self.movement_restrictions['down'] = True
                                        self.world_pos += vector(0,y_overlap)
                                    elif y_lower_2_colliding and not y_lower_1_colliding:
                                        self.movement_restrictions['up'] = True
                                        self.world_pos -= vector(0,y_overlap)
                                    else:
                                        if i.y < w.y:
                                            self.movement_restrictions['up'] = True
                                            self.world_pos -= vector(0,y_overlap)
                                        else:
                                            self.movement_restrictions['down'] = True
                                            self.world_pos += vector(0,y_overlap)
                            break

    def standard_movement(self, dt):
        if self.keys['left']:
            if not self.movement_restrictions['left'] and not self.walking['left']:
                self.walking['left'] = True
                self.velocity.x -= self.speed
        else:
            if self.walking['left']:
                self.walking['left'] = False
                self.velocity.x += self.speed
        if self.keys['right']:
            if not self.movement_restrictions['right'] and not self.walking['right']:
                self.walking['right'] = True
                self.velocity.x += self.speed
        else:
            if self.walking['right']:
                self.walking['right'] = False
                self.velocity.x -= self.speed
        if self.keys['space']:
            if not self.movement_restrictions['up'] and self.movement_restrictions['down']:
                self.velocity.y = 2*(-gravitational_acceleration*self.jump_height)**0.5
#endregion ---------------------------------------------------------------------------------------------------------------------------------------------------

#region Tween Service-----------------------------------------------------------------------------------------------------------------------------------------
def linear_tween(t,c,b,d): #t=current_time, c=change in value, b=start value, d=duration
    return c*t/d+b

def quadratic_out(t,c,b,d):
    t /= d
    return -c * t*(t-2) + b

def quadratic_in(t,c,b,d):
    t /= d
    return c*t*t + b

def quadratic_in_out(t,c,b,d):
    t /= d
    if t<1:
        return c/2*t*t + b
    t -= 1
    return - c/2 * (t*(t-2) - 1) + b

def step(dt,self):
    self.current_time += dt
    if self.vector == False:
        setattr(self.object,self.attribute,self.func(t=self.current_time,c=self.change_in_value,b=self.start_value,d=self.duration))
    else:
        if self.vector == "x":
            setattr(self.object,self.attribute,vector(self.func(t=self.current_time,c=self.change_in_value,b=self.start_value,d=self.duration),self.object.__dict__[self.attribute].y))
        elif self.vector == "y":
            setattr(self.object,self.attribute,vector(self.object.__dict__[self.attribute].x,self.func(t=self.current_time,c=self.change_in_value,b=self.start_value,d=self.duration)))
    self.current_time = self.current_time + dt
    if self.current_time >= self.duration:
        self.stop()
        if self.vector != False:
            if self.vector == "x":
                setattr(self.object,self.attribute,vector(self.target,self.object.__dict__[self.attribute].y))
            elif self.vector == "y":
                setattr(self.object,self.attribute,vector(self.object.__dict__[self.attribute].x,self.target))
        else:
            setattr(self.object,self.attribute,self.target)

tweens = {
    "Linear_Out": linear_tween, "Linear_In": linear_tween, "Linear_InOut": linear_tween, 
    "Quadratic_Out": quadratic_out, "Quadratic_In": quadratic_in, "Quadratic_InOut": quadratic_in_out
}

class tween(object):
    def __init__(self, object, attribute, target, duration = 0, easing_style = "Linear", easing_direction = "Out"):
        self.object = object
        if attribute[-2] == ".":
            self.attribute = attribute[0:-2]
            if attribute[-1] == "x":
                self.vector = "x"
            elif attribute[-1] == "y":
                self.vector = "y"
        else:
            self.attribute = attribute
            self.vector = False
        self.target = target
        self.easing_style = easing_style
        self.easing_direction = easing_direction
        self.current_time = 0
        self.start_value = None
        self.change_in_value = None
        self.duration = duration
        self.clock = None
        self.func = tweens[easing_style + "_"+easing_direction]

    def play(self):
#        for i in self.object.tweens:
#            if i.vector != False:
#                if self.vector !=False:
#
#            if i.attribute == self.attribute
        self.object.tweens.append(self)
        if self.vector != False:
            if self.vector == "x":
                self.start_value = self.object.__dict__[self.attribute].x
            if self.vector == "y":
                self.start_value = self.object.__dict__[self.attribute].y
        else:
            self.start_value = self.object.__dict__[self.attribute]
        self.change_in_value = self.target - self.start_value
        self.clock = clock.get_default()
        self.clock.schedule_interval(step, 1/120.0, self)

    def stop(self):
        self.object.tweens.remove(self)
        self.clock.unschedule(step)
        print("Tween stopped")
        del self
#endregion----------------------------------------------------------------------------------------------------------------------------------------------------

#Variables----------------------------------------------------------------------------------------------------------------------------------------------------

draw_hitboxes = True
gravitational_acceleration = -10

#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#region LOUIE'S WORKSPACE---------------------------------------------------------------------------------------------------------------------------------------------

# Load and format images
dirt_image = load_image('dirt.png')

# Generate Dirt
dirt = stage(
    img = dirt_image,
    world_pos = vector(10,0.5),
    world_size = 3,
    zindex = 100
)

dirt2 = stage(
    img = dirt_image,
    world_pos = vector(25,0.5),
    world_size = 2,
    zindex = 200
)

# Generate Sick Toad
sick_toad = world_object(
    img = load_image('sick_toad.png'),
    world_pos=vector(25,0.5),
    world_size=6,
    zindex = 100000
)

# Generate player
player_hitboxes = [hitbox(scale = vector(0.58,0.9),)]
player_hitboxes[0].opacity = 128
player = player_class(
    hitboxes=player_hitboxes,
    img=load_image("toadsworth.png"),
    jump_height=2,
    world_pos = vector(5,8),
    world_size = 4,
    zindex = 500
)

window.push_handlers(player)

#endregion---------------------------------------------------------------------------------------------------------------------------------------------------

#region Window Mapping---------------------------------------------------------------------------------------------------------------------------------------

class viewport_class(object):
    def __init__(self, position, aspect_ratio, height_meters):
        self.position = position
        self.aspect_ratio = aspect_ratio
        self.size_meters = vector(aspect_ratio*height_meters,height_meters)
        self.tweens = []

viewport = viewport_class(position = vector(0,0), aspect_ratio = 4/3, height_meters=40)
in_air = True
blackout = (window.width-math.floor(viewport.aspect_ratio*window.height))//2
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
in_frame_objects = []

def position(i):
    viewport_pixels = vector(math.floor(viewport.aspect_ratio*window.height),window.height)
    i.scale = i.world_size.y/viewport.size_meters.y*viewport_pixels.y/i.image.height
    i.x = math.floor((i.world_pos.x-i.world_size.x/2-viewport.position.x)/viewport.size_meters.x*viewport_pixels.x+i.width/2)+blackout
    i.y = math.floor((i.world_pos.y-i.world_size.y/2-viewport.position.y)/viewport.size_meters.y*viewport_pixels.y+i.height/2)

def position_hitboxes(i,width,height):
    viewport_pixels = vector(math.floor(viewport.aspect_ratio*window.height),window.height)
    i.width = width/viewport.size_meters.x*viewport_pixels.x
    i.height = height/viewport.size_meters.y*viewport_pixels.y
    i.x = math.floor((i.world_pos.x-width/2-viewport.position.x)/viewport.size_meters.x*viewport_pixels.x+i.width/2)+blackout
    i.y = math.floor((i.world_pos.y-height/2-viewport.position.y)/viewport.size_meters.y*viewport_pixels.y+i.height/2)
    i.anchor_position = (i.width//2,i.height//2)

def window_map():
    if window.height <= window.width:
        global in_air
        if player.world_pos.x > viewport.position.x + 2/3*viewport.size_meters.x:
            destination_x = player.world_pos.x - 2/3*viewport.size_meters.x
            viewport.position.x = destination_x
        elif player.world_pos.x < viewport.position.x + 1/3*viewport.size_meters.x:
            destination_x = player.world_pos.x - 1/3*viewport.size_meters.x
            viewport.position.x = destination_x
        if player.movement_restrictions['down'] and in_air:
            in_air = False
            destination_y = player.world_pos.y - 1/6*viewport.size_meters.y
            if destination_y != viewport.position.y:
                viewport_tween = tween(
                object=viewport,
                attribute="position.y",
                target=destination_y,
                duration=(abs(destination_y-viewport.position.y))/1,
                easing_style="Quadratic",
                easing_direction="Out"
                )
                viewport_tween.play()
        elif not player.movement_restrictions['down'] and not in_air:
            in_air = True
        local_in_frame_objects = []
        viewport.size_meters.x = viewport.size_meters.y*viewport.aspect_ratio
        for i in objects:
            upper_x, lower_x = i.world_pos.x + i.world_size.x/2, i.world_pos.x - i.world_size.x/2
            upper_y, lower_y = i.world_pos.y + i.world_size.y/2, i.world_pos.y - i.world_size.y/2
            if (((upper_x >= viewport.position.x and upper_x <= viewport.position.x + viewport.size_meters.x) or (lower_x >= viewport.position.x and lower_x <= viewport.position.x + viewport.size_meters.x)) or (lower_x < viewport.position.x and upper_x > viewport.position.x + viewport.size_meters.x)) and (((upper_y >= viewport.position.y and upper_y <= viewport.position.y + viewport.size_meters.y) or (lower_y >= viewport.position.y and lower_y <= viewport.position.y + viewport.size_meters.y)) or (lower_x < viewport.position.x and upper_x > viewport.position.x + viewport.size_meters.y)):
                position(i)
                local_in_frame_objects.append(i)
            if draw_hitboxes and hasattr(i,"hitboxes"):
                for w in i.hitboxes:
                    width = w.world_size.x
                    height = w.world_size.y
                    position_hitboxes(w,width,height)
                    local_in_frame_objects.append(w)
        global in_frame_objects
        in_frame_objects = local_in_frame_objects

background = pyglet.shapes.Rectangle(
    width = window.width,
    height = window.height,
    x=0,y=0,
    color=(50,50,50)
)
@window.event
def on_resize(width,height):
    #resize the blackouts and background
    background.width = width
    background.height = height
    global blackout
    blackout = (width-viewport.aspect_ratio*height)//2
    left_shade.height = height
    right_shade.height = height
    left_shade.width = blackout
    right_shade.width = blackout
    right_shade.x = width-blackout

#endregion---------------------------------------------------------------------------------------------------------------------------------------------------

#region Event Cycle------------------------------------------------------------------------------------------------------------------------------------------
def central_clock(dt):
    for i in physical_objects:
        if not i.anchored:
            i.update(dt)
    player.standard_movement(dt)
    player.check_collisions(stage_objects,dt)
    window_map()

clock.schedule_interval(central_clock, 1/120.0)

def sort_z_indices(obj):
    if hasattr(obj,"zindex"):
        return obj.zindex
    else:
        return float('inf')

# Draw objects
@window.event
def on_draw():
    window.clear()
    background.draw()
    in_frame_objects.sort(key=sort_z_indices)
    for i in in_frame_objects:
        i.draw()
    if draw_hitboxes:
        hitboxes.draw()
    left_shade.draw()
    right_shade.draw()

#endregion---------------------------------------------------------------------------------------------------------------------------------------------------

pyglet.app.run()