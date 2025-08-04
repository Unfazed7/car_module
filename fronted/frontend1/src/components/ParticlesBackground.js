import React from 'react';
import Particles from 'react-tsparticles';
import { loadFull } from 'tsparticles';

function ParticlesBackground() {
  const particlesInit = async (main) => {
    await loadFull(main);
  };

  return (
    <Particles
      id="tsparticles"
      init={particlesInit}
      options={{
        background: {
          color: "#000"
        },
        fpsLimit: 60,
        interactivity: {
          events: {
            onClick: { enable: false },
            onHover: { enable: false },
            resize: true,
          },
        },
        particles: {
          color: { value: "#00f0ff" },
          links: {
            enable: true,
            color: "#00f0ff",
            distance: 120,
            opacity: 0.2,
            width: 1,
          },
          move: {
            enable: true,
            speed: 0.5,
            direction: "none",
            outMode: "bounce",
          },
          number: {
            value: 60,
            density: { enable: true, area: 800 },
          },
          opacity: { value: 0.4 },
          size: { value: 1.8 },
        },
        detectRetina: true,
      }}
    />
  );
}

export default ParticlesBackground;
