import React, { useRef, useEffect, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, useGLTF, useAnimations } from '@react-three/drei';
import * as THREE from 'three';

function CarModel({ animationNames, reverse }) {
  const group = useRef();
  const { scene, animations: clips } = useGLTF('/car.glb'); // ✅ renamed to clips
  const { actions } = useAnimations(clips, group); // ✅ bind to ref group
  //const animationNames =Object.keys(actions);
  const lastActions = useRef([]);
	
  useEffect(() => {
    console.log("🎞️ Loaded animation clips:", clips.map(a => a.name));
  }, [clips]);

  useEffect(() => {
    console.log("🧪 CarModel useEffect triggered with:", animationNames, reverse);
    console.log("🎬 Available clips:", Object.keys(actions));

    if (!animationNames || animationNames.length === 0) return;

    // Stop previous animations
    //lastActions.current.forEach(a => a.stop());
    //lastActions.current = [];

    animationNames.forEach(name => {
      const action = actions[name];
      if (!action) {
        console.warn(`⚠️ Animation "${name}" not found.`);
        return;
      }

      action.reset();
      action.setLoop(THREE.LoopOnce, 1);
      action.clampWhenFinished = true;

      if (reverse) {
        action.timeScale = -1;
        action.paused = false;
        action.time = action.getClip().duration;
      } else {
        action.timeScale = 1;
      }

      action.play();
      lastActions.current.push(action);
    });
  }, [JSON.stringify(animationNames), reverse]);

  return (
    <primitive
      ref={group}
      object={scene}
      scale={1.5}
      position={[0, -1.5, 0]}
      rotation={[0, Math.PI, 0]}
    />
  );
}

export default function CarViewer({ animations = [], reverse }) {
  useEffect(() => {
    console.log("📦 CarViewer received animations:", animations);
  }, [animations, reverse]);

  return (
    <Canvas camera={{ position: [0, 2, 5], fov: 45 }}>
      <ambientLight intensity={0.6} />
      <directionalLight position={[0, 5, 5]} />
      <OrbitControls enablePan={false} />
        
        <Suspense fallback={null}>
        <CarModel animationNames={animations} reverse={reverse} />
      
        <Environment preset="warehouse" background />
      </Suspense>
    </Canvas>
  );
}

