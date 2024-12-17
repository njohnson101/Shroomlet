Shroomlet is a basic 2d physics system for video game development in Python. It is built off of Pyglet, an open source library for visual applications. Shroomlet adds physical object classes and viewport functionality that streamlines worldbuilding. Full documentation is available [here](https://docs.google.com/document/d/10B9kkgwoIRtmVP0GlCZPT6sJkjEB-sfSxxwadtiBjUo/edit?usp=sharing).

This was part of an unreleased passion project, so it is certainly far from a finished product; however, it was a lot of fun to program, so I thought I’d clean it up and share it here! 

At the time, I was working on a small team as the most experienced programmer, and as I built the physics and rendering system, I wanted other developers on the team (especially the asset artists) to be able to craft worlds and test as they went. To this end, I created a set of simple objects with easy-to-understand attributes that allowed them to implement their assets without much programming knowledge.

The script includes three major sections: the core of Shroomlet (where object classes, functions and the like are defined), the workspace, and the event cycle. The workspace is where all objects are created, and where the developer is able to enjoy a simpler world building process.

The workspace currently includes three areas to experiment with:
1. plain; exactly as it sounds, a platform of grass to demonstrate basic functionality.
2. playground; this is simply the plain with two brick walls to experiment with wall jumps, a wholly unfinished mechanic but a fun one to program nonetheless.
3. firefly_cottage; this area includes the most assets. It was home to a character named “Firefly” in the aforementioned passion project.

If I were to devote more time to this project, I would explore ways to compress “domains” into easily accessible data stores. Domains in Shroomlet are collections of objects that exist distinctly from each other within the video game (you might think of them as different “worlds”). These domains are defined as simple lists of objects, so I am intrigued by the idea of saving these lists outside of the main script and accessing them individually as the game demands. To complete the potential of this, I would also explore how to move the “workspace” section outside of the Shroomlet program so that Shroomlet can operate as a proper library.

Through this project, I learned a great deal more about objects in Python and how they interact with each other. I also had practice developing a system with consistent standards throughout, ensuring that each new piece of code is able to interact properly with the larger program.
