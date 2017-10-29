class Particle:
    def __init__(self, particleImage, particleSpeedVector, particleLifetimeSeconds, startingLocation, inputFrame,
                 frameFPS=60):
        # In the form of (xSpeed, ySpeed), speed can be positive or negative.
        self.speedVector = particleSpeedVector

        self.image = particleImage
        self.lifetimeSeconds = particleLifetimeSeconds
        self.currentLocation = startingLocation
        self.fps = frameFPS
        self.currentFrame = inputFrame

    def updateParticle(self):
        print()
