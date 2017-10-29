class ParticleEffect:
    def __init__(self, particleEffectImage, lifetimeSeconds, amountToGenerate):
        self.effectImage = particleEffectImage
        self.lifetimeSeconds = lifetimeSeconds
        self.amountToGenerate = amountToGenerate
        # Amount of particles to generate per second
