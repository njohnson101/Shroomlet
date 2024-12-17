#region Setup---------------------------------------------------------------------------------------------------------------------------------------------------
import pyglet
import math
mouse = pyglet.window.mouse
clock = pyglet.clock

hitboxes = pyglet.graphics.Batch()

window = pyglet.window.Window(fullscreen=True)
window.set_caption('Shroomlet')

pyglet.resource.path = ['.','NolanSuckDuck/Assets']
pyglet.resource.reindex()

def load_image(image):
    img = pyglet.resource.image(image)
    img.anchor_x = img.width//2
    img.anchor_y = img.height//2
    return img

def check_tweens(self,key,tweened):
    if not tweened:
        for i in self.tweens:
            if i.attribute == key:
                i.stop()

#endregion ----------------------------------------------------------------------------------------------------------------------------------------------------

#  Variables----------------------------------------------------------------------------------------------------------------------------------------------------

draw_hitboxes = False
viewport_height = 8
gravitational_acceleration = -10
terminal_velocity = -50
wall_friction = 5
ground_friction = 2  #counterforce to velocity. Essentially the velocity applied in the other direction when coming to a stop/turning. p/s (players/second)
air_friction = 5

#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#region Initialize Areas--------------------------------------------------------------------------------------------------------------------------------------
class domain(object):
    def __init__(self,auto_pan_x = True,auto_pan_y = True,upper_bound_x = math.inf,lower_bound_x = -math.inf,upper_bound_y = math.inf,lower_bound_y = -math.inf):
        self.objects = []
        self.physical_objects = []
        self.backgrounds = []
        self.auto_pan_x = auto_pan_x
        self.auto_pan_y = auto_pan_y
        self.upper_bound_x = upper_bound_x
        self.upper_bound_y = upper_bound_y
        self.lower_bound_x = lower_bound_x
        self.lower_bound_y = lower_bound_y

    def remove(self,target):
        if target in self.objects:
            self.objects.remove(target)
        if target in self.physical_objects:
            self.physical_objects.remove(target)
        if target in self.backgrounds:
            self.backgrounds.remove(target)
    
    def append(self,target):
        cname = target.__class__.__name__
        if cname == "stage" or cname == "physical_object" or cname == "player_class":
            self.objects.append(target)
            self.physical_objects.append(target)
        elif cname == "background_object":
            self.objects.append(target)
            self.backgrounds.append(target)
        elif cname == "world_object":
            self.objects.append(target)
    
    def transfer(self,target,new_area):
        self.remove(target)
        new_area.append(target)

    def __str__(self):
        return "objects: "+str(self.objects)+"\n"+"physical objects: "+str(self.physical_objects)+"\n"+"backgrounds: "+str(self.backgrounds)



area = domain()
editing_area = None
#endregion -----------------------------------------------------------------------------------------------------------------------------------------------------

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

anim_clocks = []

def anim_step(dt, self):
    self.timer += dt
    change = False
    while self.timer-self.last_change >= self.track.frames[self.current_frame]["duration"]:
        change = True
        self.last_change += self.track.frames[self.current_frame]["duration"]
        self.current_frame += 1
        if self.current_frame == len(self.track.frames):
            self.current_frame = 0
    if change:
        self.target.image = self.track.frames[self.current_frame]["image"]

class frame_sequence(object):
    def __init__(self, frames, duration = None):
        self.duration = duration
        self.frames = frames

    def __setattr__(self, key, value):
        if key == "frames":
            tofu = []
            if self.duration != None:
                for i in value:
                    tofu.append({"image":i,"duration":self.duration})
            else:
                tofu = value
            self.__dict__["frames"] = tofu
        else:
            self.__dict__[key] = value

class animation(object):
    def __init__(self, track, target, loop=True):
        self.track = track
        self.playing = False
        self.timer = 0
        self.last_change = 0
        self.current_frame = 0
        self.target = target
        self.loop = loop
        self.clock = None

    def play(self):
        if not self.playing:
            self.playing = True
            self.clock = clock.Clock()
            self.clock.schedule(anim_step, self)
            anim_clocks.append(self.clock)

    def pause(self):
        self.playing = False
        self.clock.unschedule(anim_step)
        anim_clocks.remove(self.clock)
        del self.clock

    def reset(self):
        self.timer = 0
        self.last_change = 0
        self.current_frame = 0
    
    def stop(self):
        self.pause()
        self.reset()

class world_object(object):
    def __init__(self, world_pos = vector(0,0), world_size=0, zindex=1, supered=False, *args, **kwargs):
        self.__dict__["tweens"] = []
        self.__dict__["sprite"] = pyglet.sprite.Sprite(x=0,y=0,*args,**kwargs)
        self.__dict__["zindex"] = zindex
        self.__dict__["world_pos"] = world_pos
        if supered:
            self.__dict__["world_size"] = world_size
        else:
            self.world_size = world_size
        editing_area.objects.append(self)

    def __setattr__(self, key, value, tweened=False,supered=False):
        if not supered:
            check_tweens(self,key,tweened)
        if key == "world_size":
            if value.__class__.__name__ != "vector":
                self.__dict__["world_size"] = vector(self.image.width/self.image.height*value, value)
            else:
                self.__dict__["world_size"] = value
        elif key == "image":
            sx = self.sprite.scale_x
            sy = self.sprite.scale_y
            spr = pyglet.sprite.Sprite(img=value,x=self.sprite.x,y=self.sprite.y)
            spr.scale_x = sx
            spr.scale_y = sy
            self.sprite = spr

        elif key in self.__dict__:
            self.__dict__[key] = value
        else:
            self.sprite.__setattr__(key,value)
    
    def __getattr__(self, key):
        if key == "image":
            return self.sprite.image
        elif key == "width":
            return self.sprite.width
        elif key == "height":
            return self.sprite.height
        else:
            return self.sprite.__dict__["_"+key]
        
    def transfer_domain(self, current, target):
        current.remove(self)
        target.append(self)


class background_object(world_object):
    def __init__(self, distance = 2,*args, **kwargs):
        super().__init__(supered=True,*args,**kwargs)
        self.__dict__["distance"] = distance
        self.world_size = self.world_size
        editing_area.backgrounds.append(self)

class physical_object(world_object):
     
    def __init__(self, hitboxes = None, velocity = vector(0,0), gravitational_pull = gravitational_acceleration, terminal_pull = terminal_velocity, anchored = True, supered=False, *args, **kwargs):
        super().__init__(supered=True,*args,**kwargs)
        if hitboxes == None:
            self.__dict__["hitboxes"] = [hitbox()]
        else:
            self.__dict__["hitboxes"] = hitboxes
        for i in self.hitboxes:
            i.color = (0,0,255)
            i.parent = self
        if supered:
            self.__dict__["world_size"] = self.world_size
        else:
            self.world_size = self.world_size
        self.__dict__["gravitational_pull"] = gravitational_pull
        self.__dict__["terminal_pull"] = terminal_pull
        self.__dict__["velocity"] = velocity
        self.__dict__["anchored"] = anchored
        if not supered:
            editing_area.physical_objects.append(self)

    def update_hitboxes(self):
        for i in self.hitboxes:
            i.world_pos = vector(self.world_pos.x + self.world_size.x*i.offset.x, self.world_pos.y + self.world_size.y*i.offset.y)
            i.world_size = vector(self.world_size.x*i.scale.x, self.world_size.y*i.scale.y)

    def __setattr__(self, key, value, tweened=False):
        check_tweens(self,key,tweened)
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
            super().__setattr__(key, value, supered=True)

    def update(self,dt):
        """ if self.__class__.__name__ == "player_class":
            print(self.gravitational_pull)
            print(self.terminal_pull) """
        if not self.movement_restricted('down') and self.velocity.y > self.terminal_pull:
            self.velocity.y += 2*self.gravitational_pull*dt
            if self.velocity.y < self.terminal_pull:
                self.velocity.y = self.terminal_pull
        elif self.movement_restricted('down') and self.velocity.y<0:
            self.velocity.y = 0
        x_update, y_update = 0,0
        if self.velocity.x < 0:
            if not self.movement_restricted('left'):
                x_update = self.velocity.x * dt
            else:
                self.velocity.x = 0
                x_update = 0
        elif self.velocity.x > 0:
            if not self.movement_restricted('right'):
                x_update = self.velocity.x * dt
            else:
                self.velocity.x = 0
                x_update = 0
        if self.velocity.y < 0 and not self.movement_restricted('down'):
            y_update = self.velocity.y * dt
        elif self.velocity.y > 0 and not self.movement_restricted('up'):
            y_update = self.velocity.y * dt
        self.world_pos += vector(x_update, y_update)

class stage(physical_object):

    def __init__(self, *args, **kwargs):
        super().__init__(supered=True,*args,**kwargs)
        self.world_size = self.world_size
        for i in self.hitboxes:
            i.color=(139,69,19)
        editing_area.physical_objects.append(self)

cassie_left_walk = frame_sequence(frames = [load_image("cassie_walk_1.png"),
    load_image("cassie_walk_2.png"),
    load_image("cassie_walk_3.png"),
    load_image("cassie_walk_4.png"),
    load_image("cassie_walk_5.png"),
    load_image("cassie_walk_6.png"),
    load_image("cassie_walk_7.png"),
    load_image("cassie_walk_8.png")],
    duration = 0.2)

cassie_right_walk = frame_sequence(frames = [load_image("cassie_walk_1r.png"),
    load_image("cassie_walk_2r.png"),
    load_image("cassie_walk_3r.png"),
    load_image("cassie_walk_4r.png"),
    load_image("cassie_walk_5r.png"),
    load_image("cassie_walk_6r.png"),
    load_image("cassie_walk_7r.png"),
    load_image("cassie_walk_8r.png")],
    duration = 0.2)

cassie_idle_left = load_image("cassie_walk_4.png")
cassie_idle_right = load_image("cassie_walk_4r.png")

class player_class(physical_object):
    def __init__(self, speed=10, acceleration=5, jump_height=0, life = 100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in self.hitboxes:
            i.color = (0,255,0)
        self.__dict__["keys"] = dict(left=False, right=False, space=False)
        self.__dict__["facing"] = True  #True if facing right, false if facing left
        self.__dict__["walking"] = False
        self.__dict__["walk"] = animation(
                                    cassie_left_walk,
                                    target=self
                                )
        self.__dict__["dominant_key"] = None
        self.__dict__["acceleration"] = acceleration
        self.__dict__["speed"] = speed # max velocity
        self.__dict__["jump_height"] = jump_height
        self.__dict__["life"] = life
        self.__dict__["collisions"] = []
        self.__dict__["right_clung"] = False
        self.__dict__["left_clung"] = False
        self.__dict__["anchored"] = False
        self.world_size = self.world_size
    
    def on_key_press(self, button, modifiers):
        if button == key.LEFT:
            self.keys['left'] = True
            if self.keys['right']:
                self.dominant_key = 'right'
        elif button == key.RIGHT:
            self.keys['right'] = True
            if self.keys['left']:
                self.dominant_key = 'left'
        elif button == key.SPACE:
            self.keys['space'] = True

    def on_key_release(self, button, modifiers):
        if button == key.LEFT:
            self.keys['left'] = False
            self.dominant_key = None
        elif button == key.RIGHT:
            self.keys['right'] = False
            self.dominant_key = None
        elif button == key.SPACE:
            self.keys['space'] = False

    def movement_restricted(self,direction):
        for i in self.collisions:
            if direction == i["direction"]:
                return True

    def check_collisions(self, objs, dt):
        hitboxes = self.hitboxes
        self.collisions = []
        for i in hitboxes:
            x_lower_1, x_upper_1 = i.world_pos.x - i.world_size.x/2, i.world_pos.x + i.world_size.x/2
            y_lower_1, y_upper_1 = i.world_pos.y - i.world_size.y/2, i.world_pos.y + i.world_size.y/2
            for m in objs:
                if m!=self:
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
#                                if m.__class__.__name__ == "physical_object":
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
                                        self.collisions.append({"object":i,"direction":"right"})
                                        self.world_pos -= vector(x_overlap,0)
                                    elif x_lower_1_colliding and not x_lower_2_colliding:
                                        self.collisions.append({"object":i,"direction":"left"})
                                        self.world_pos += vector(x_overlap,0)
                                    else:
                                        if i.x < w.x:
                                            self.collisions.append({"object":i,"direction":"right"})
                                            self.world_pos -= vector(x_overlap,0)
                                        else:
                                            self.collisions.append({"object":i,"direction":"left"})
                                            self.world_pos += vector(x_overlap,0,)
                                else:
                                    if y_lower_1_colliding and not y_lower_2_colliding:
                                        self.collisions.append({"object":i,"direction":"down"})
                                        self.world_pos += vector(0,y_overlap)
                                    elif y_lower_2_colliding and not y_lower_1_colliding:
                                        self.collisions.append({"object":i,"direction":"up"})
                                        self.world_pos -= vector(0,y_overlap)
                                    else:
                                        if i.y < w.y:
                                            self.collisions.append({"object":i,"direction":"up"})
                                            self.world_pos -= vector(0,y_overlap)
                                        else:
                                            self.collisions.append({"object":i,"direction":"down"})
                                            self.world_pos += vector(0,y_overlap)
                                break

    def standard_movement(self, dt): # WALL JUMPS NEED TO ONLY WORK WITH STAGE OBJECTS
        if self.keys['left']:
            if not self.movement_restricted("left") and self.dominant_key != "right":
                if self.facing:
                    self.facing = False
                    self.walk.track = cassie_left_walk
                if not self.walking:
                    self.walking = True
                    self.walk.play()
                if self.velocity.x > -self.speed:
                    self.velocity.x -= self.acceleration*dt
                    if self.velocity.x < -self.speed:
                        self.velocity.x = -self.speed
            elif self.movement_restricted('left') and not self.left_clung and self.velocity.y<=-2:
                self.left_clung = True
                self.gravitational_pull = 0
                self.velocity.y = -2
        elif self.keys['right']:
            if not self.movement_restricted("right") and self.dominant_key != "left":
                if not self.facing:
                    self.facing = True
                    self.walk.track = cassie_right_walk
                if not self.walking:
                    self.walking = True
                    self.walk.play()
                if self.velocity.x < self.speed:
                    self.velocity.x += self.acceleration*dt
                    if self.velocity.x > self.speed:
                        self.velocity.x = self.speed
            elif self.movement_restricted('right') and not self.right_clung and self.velocity.y<=-2:
                self.right_clung = True
                self.gravitational_pull = 0
                self.velocity.y = -2
        else:
            if self.velocity.x < 0:
                self.velocity.x += self.acceleration*dt
                if self.velocity.x > 0:
                    self.velocity.x = 0
            elif self.velocity.x > 0:
                self.velocity.x -= self.acceleration*dt
                if self.velocity.x < 0:
                    self.velocity.x = 0
            if self.walking:
                self.walking = False
                self.walk.stop()
                if self.facing:
                    self.image = cassie_idle_right
                else:
                    self.image = cassie_idle_left

        if self.keys['space']:
            if not self.movement_restricted("up"):
                if self.movement_restricted('down'):
                    self.velocity.y = 2*(-gravitational_acceleration*self.jump_height)**0.5
                elif self.left_clung:
                    self.left_clung = False
                    self.gravitational_pull = gravitational_acceleration
                    self.velocity.x = self.speed
                    self.velocity.y = 2*(-gravitational_acceleration*self.jump_height)**0.5
                elif self.right_clung:
                    self.right_clung = False
                    self.gravitational_pull = gravitational_acceleration
                    self.velocity.x = -self.speed
                    self.velocity.y = 2*(-gravitational_acceleration*self.jump_height)**0.5

#endregion ---------------------------------------------------------------------------------------------------------------------------------------------------

#region Tween Service-----------------------------------------------------------------------------------------------------------------------------------------
tween_clocks = []

def linear_tween(t,c,b,d): #t=current_time, c=change in value, b=start value, d=duration
    return c*t/d+b

def quadratic_out(t,c,b,d):
    w = t/d
    return -c * w*(w-2) + b

def quadratic_in(t,c,b,d):
    w = t/d
    return c*w*w + b

def quadratic_in_out(t,c,b,d):
    w = t/d
    if w<1:
        return c/2*w*w + b
    w = w-1
    return - c/2 * (w*(w-2) - 1) + b

def step(dt,self):
    if self.vector == False:
        self.object.__setattr__(self.attribute,self.func(t=self.current_time,c=self.change_in_value,b=self.start_value,d=self.duration),tweened=True)
    else:
        if self.vector == "x":
            self.object.__setattr__(self.attribute,vector(self.func(t=self.current_time,c=self.change_in_value,b=self.start_value,d=self.duration),self.object.__dict__[self.attribute].y),tweened=True)
        elif self.vector == "y":
            self.object.__setattr__(self.attribute,vector(self.object.__dict__[self.attribute].x,self.func(t=self.current_time,c=self.change_in_value,b=self.start_value,d=self.duration)),tweened=True)
    self.current_time = self.current_time + dt
    if self.current_time >= self.duration:
        self.stop()
        if self.vector != False:
            if self.vector == "x":
                self.object.__setattr__(self.attribute,vector(self.target,self.object.__dict__[self.attribute].y),tweened=True)
            elif self.vector == "y":
                self.object.__setattr__(self.attribute,vector(self.object.__dict__[self.attribute].x,self.target),tweened=True)
        else:
            self.object.__setattr__(self.attribute,self.target,tweened=True)

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
        self.object.tweens.append(self)
        if self.vector != False:
            if self.vector == "x":
                self.start_value = self.object.__dict__[self.attribute].x
            if self.vector == "y":
                self.start_value = self.object.__dict__[self.attribute].y
        else:
            self.start_value = self.object.__getattribute__(self.attribute)
        self.change_in_value = self.target - self.start_value
        self.clock = clock.Clock()
        self.clock.schedule(step, self)
        tween_clocks.append(self.clock)

    def stop(self):
        self.object.tweens.remove(self)
        self.clock.unschedule(step)
        tween_clocks.remove(self.clock)
        del self.clock
        del self
#endregion ----------------------------------------------------------------------------------------------------------------------------------------------------

#region Window Mapping---------------------------------------------------------------------------------------------------------------------------------------

class viewport_class(object): #position from bottom left of screen
    def __init__(self, position, aspect_ratio, height_meters):
        self.__dict__["tweens"] = []
        self.__dict__["position"] = position
        self.aspect_ratio = aspect_ratio
        self.size_meters = vector(aspect_ratio*height_meters,height_meters)
    
    def __setattr__(self, key, value, tweened=False):
        check_tweens(self,key,tweened)
        if key == "position":
            delta = value - self.position
            for i in area.backgrounds:
                i.world_pos += delta/i.distance
        self.__dict__[key] = value


viewport = viewport_class(position = vector(0,0), aspect_ratio = 4/3, height_meters=viewport_height)
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
    i.scale_y = i.world_size.y/viewport.size_meters.y*viewport_pixels.y/i.image.height
    i.scale_x = i.world_size.x/viewport.size_meters.x*viewport_pixels.x/i.image.width
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
        if area.auto_pan_x:
            if player.world_pos.x > viewport.position.x + 2/3*viewport.size_meters.x:
                destination_x = player.world_pos.x - 2/3*viewport.size_meters.x
                if destination_x>area.upper_bound_x-viewport.size_meters.x:
                    print("reached max x value")
                    viewport.position = vector(area.upper_bound_x-viewport.size_meters.x,viewport.position.y)
                else:
                    print("updating to destination")
                    viewport.position = vector(destination_x,viewport.position.y)
            elif player.world_pos.x < viewport.position.x + 1/3*viewport.size_meters.x:
                destination_x = player.world_pos.x - 1/3*viewport.size_meters.x
                if destination_x<area.lower_bound_x:
                    print("reached min x value")
                    viewport.position = vector(area.lower_bound_x,viewport.position.y)
                else:
                    print("updating to destination")
                    viewport.position = vector(destination_x,viewport.position.y)
        if area.auto_pan_y:
            if player.movement_restricted('down') and in_air:
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
            elif not player.movement_restricted('down') and not in_air:
                in_air = True
        local_in_frame_objects = []
        viewport.size_meters.x = viewport.size_meters.y*viewport.aspect_ratio
        for i in area.objects:
            upper_x, lower_x = i.world_pos.x + i.world_size.x/2, i.world_pos.x - i.world_size.x/2
            upper_y, lower_y = i.world_pos.y + i.world_size.y/2, i.world_pos.y - i.world_size.y/2
            if (((upper_x >= viewport.position.x and upper_x <= viewport.position.x + viewport.size_meters.x) or (lower_x >= viewport.position.x and lower_x <= viewport.position.x + viewport.size_meters.x)) or (lower_x < viewport.position.x and upper_x > viewport.position.x + viewport.size_meters.x)) and (((upper_y >= viewport.position.y and upper_y <= viewport.position.y + viewport.size_meters.y) or (lower_y >= viewport.position.y and lower_y <= viewport.position.y + viewport.size_meters.y)) or (lower_y < viewport.position.y and upper_y > viewport.position.y + viewport.size_meters.y)):
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

#endregion ---------------------------------------------------------------------------------------------------------------------------------------------------

#region WORKSPACE---------------------------------------------------------------------------------------------------------------------------------------------


plain = domain()
editing_area = plain

# Load and format images
dirt_image = load_image('dirt.png')

# Generate Dirt
dirt1 = stage(
    img = dirt_image,
    world_pos = vector(10,0.5),
    world_size = 3,
    zindex = 100
)



playground = domain()
print(viewport.position)
viewport.position = vector(0,0)
print(viewport.position)
viewport.size_meters = vector(viewport.aspect_ratio*3,3)
editing_area = playground

dirt = stage(
    img = dirt_image,
    world_pos = vector(10,0.5),
    world_size = 3,
    zindex = 100
)


bricks_image = load_image('bricks.webp')

bricks = stage(
    img = bricks_image,
    world_pos = vector(10.2,10),
    world_size = vector(1,20),
    zindex = 400
)

bricks2 = stage(
    img = bricks_image,
    world_pos = vector(12.8,10),
    world_size = vector(1,20),
    zindex = 400
)

oberma = background_object(
    img = load_image("obama.png"),
    world_pos = vector(10,0),
    world_size = 10,
    distance = 1.5
)


firefly_cottage = domain(auto_pan_y = False,upper_bound_x = 2.07,lower_bound_x = -2.95)
print(viewport.position)
viewport.position = vector(-100,0)
print(viewport.position)
viewport.size_meters = vector(viewport.aspect_ratio*3,3)

editing_area = firefly_cottage

floor_image = load_image("WoodFloor.PNG")

wall = world_object(
    img = load_image("Bedroom.png"),
    world_pos = vector(-0.5,1.65),
    world_size = 2.8, #5.6
    zindex = 10
)

def jamaica():
    return {hitbox(scale=vector(1,0.5),offset=vector(0,-0.25))}

floor = physical_object(
    img = floor_image,
    world_pos = vector(0,0.15),
    world_size = 0.3,
    hitboxes=jamaica(),
    zindex = 50
)
floor_again = physical_object(
    img = floor_image,
    world_pos = vector(4,0.15),
    world_size = 0.3,
    hitboxes=jamaica(),
    zindex = 50
)
floor_but_again = physical_object(
    img = floor_image,
    world_pos = vector(-4,0.15),
    world_size = 0.3,
    hitboxes=jamaica(),
    zindex = 50
)
floor_redux = physical_object(
    img = floor_image,
    world_pos = vector(-4,0.15),
    world_size = 0.3,
    hitboxes=jamaica(),
    zindex = 50
)
bed = world_object(
    img = load_image("Bed.PNG"),
    world_pos = vector(1.2,0.5),
    world_size = 0.7,
    zindex = 100
)
stool = world_object(
    img = load_image("Stool.PNG"),
    world_pos = vector(1.75,0.3),
    world_size = 0.5,
    zindex = 200
)
lamp = world_object(
    img = load_image("LampOff.png"),
    world_pos = vector(1.75,0.75),
    world_size = 0.5,
    zindex = 300
)
picture_frames = world_object(
    img = load_image("Photos.png"),
    world_pos = vector(1.2,2),
    world_size = 1.2,
    zindex = 25
)
curtains = world_object(
    img = load_image("Curtains.PNG"),
    world_pos = vector(-1.77,2),
    world_size = 1.2,
    zindex = 25
)


print(firefly_cottage)


# Generate player
player_hitboxes = [hitbox(scale = vector(0.58,0.9),)]
player_hitboxes[0].opacity = 128
player = player_class(
    hitboxes=player_hitboxes,
    img=load_image("cassie_walk_4.png"),
    jump_height=1.5,
    world_pos = vector(0,2),
    world_size = 1,
    speed = 5,
    acceleration=20, #CURRENTLY, ONLY ACCELERATION DECIDES TURN AROUND TIME. THIS IS TEMPORARY; MUST ADD INTO ACCOUNT DIFFERENCE BETWEEN AIR AND GROUND (FRICTION)
    zindex = 500
)

window.push_handlers(player)

player.speed = 2
player.jump_height = 0.8
area = firefly_cottage

#Remove apostraphes to test out the playground:

area = playground
player.transfer_domain(firefly_cottage, playground)
player.world_pos = vector(11.5,2)
player.speed = 3
viewport.size_meters = vector(viewport.aspect_ratio*5,5)


#Remove apostraphes to test out the plain:
'''
area = plain
player.transfer_domain(firefly_cottage, plain)
player.world_pos = vector(11.5,2)
player.speed = 3
viewport.size_meters = vector(viewport.aspect_ratio*5,5)
'''

#endregion ---------------------------------------------------------------------------------------------------------------------------------------------------

#region Event Cycle------------------------------------------------------------------------------------------------------------------------------------------
def central_clock(dt):
    for i in tween_clocks:
        i.tick()
    for i in anim_clocks:
        i.tick()
    for i in area.physical_objects:
        if not i.anchored:
            i.update(dt)
    player.standard_movement(dt)
    player.check_collisions(area.physical_objects,dt)
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
        i.sprite.draw()
    if draw_hitboxes:
        hitboxes.draw()
    left_shade.draw()
    right_shade.draw()

#endregion ---------------------------------------------------------------------------------------------------------------------------------------------------

pyglet.app.run()