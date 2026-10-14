'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Sparkles } from 'lucide-react';

interface PaperNode {
  title: string;
  category: string;
  citations: number;
}

const MOCK_PAPERS: PaperNode[] = [
  { title: "Attention Is All You Need", category: "Deep Learning", citations: 12420 },
  { title: "LLaMA: Open Foundation Models", category: "NLP", citations: 3120 },
  { title: "Deep Residual Learning (ResNet)", category: "Computer Vision", citations: 8520 },
  { title: "Generative Adversarial Nets", category: "GANs", citations: 9410 },
  { title: "Adam: A Method for Stochastic Optimization", category: "Optimization", citations: 15400 },
  { title: "BERT: Pre-training of Deep Bidirectional Transformers", category: "NLP", citations: 11450 },
  { title: "ImageNet Classification with Deep CNNs", category: "Computer Vision", citations: 18900 }
];

export default function ThreeCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredPaper, setHoveredPaper] = useState<PaperNode | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // 1. Scene setup
    const scene = new THREE.Scene();

    // 2. Camera setup
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 100);
    camera.position.z = 12;

    // 3. Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    containerRef.current.appendChild(renderer.domElement);

    // 4. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // 5. Build Knowledge Graph Nodes
    const nodesGroup = new THREE.Group();
    scene.add(nodesGroup);

    const nodeGeometry = new THREE.SphereGeometry(0.35, 32, 32);
    const colors = [0x6366f1, 0xec4899, 0x3b82f6, 0x8b5cf6, 0x10b981];

    const nodeMeshes: THREE.Mesh[] = [];

    MOCK_PAPERS.forEach((paper, i) => {
      const color = colors[i % colors.length];
      const material = new THREE.MeshPhongMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.15,
        shininess: 30,
        specular: 0xffffff,
      });

      const mesh = new THREE.Mesh(nodeGeometry, material);
      
      // Arrange in a nice 3D spatial layout
      const angle = (i / MOCK_PAPERS.length) * Math.PI * 2;
      const radius = 3.5 + Math.random() * 0.8;
      mesh.position.set(
        Math.cos(angle) * radius,
        (Math.random() - 0.5) * 3,
        Math.sin(angle) * radius
      );

      // Attach data to user data for raycaster extraction
      mesh.userData = { paperIndex: i };
      nodesGroup.add(mesh);
      nodeMeshes.push(mesh);
    });

    // 6. Build Connection Lines
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x6366f1,
      transparent: true,
      opacity: 0.25,
    });

    const points: THREE.Vector3[] = [];
    // Connect nodes sequentially and some cross-connections
    for (let i = 0; i < nodeMeshes.length; i++) {
      const nodeA = nodeMeshes[i].position;
      const nextIndex = (i + 1) % nodeMeshes.length;
      const nodeB = nodeMeshes[nextIndex].position;
      points.push(nodeA, nodeB);

      // Cross connections
      if (i % 2 === 0) {
        const crossIndex = (i + 3) % nodeMeshes.length;
        const nodeC = nodeMeshes[crossIndex].position;
        points.push(nodeA, nodeC);
      }
    }

    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    nodesGroup.add(lines);

    // 7. Raycasting & Mouse Tracker
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let currentHoveredMesh: THREE.Mesh | null = null;

    const handleMouseMove = (event: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      
      // Normalized device coordinates
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      // Track raw client coordinates to float tooltip
      setMousePos({ x: event.clientX, y: event.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);

    // 8. Animation & Render Loop
    let animationFrameId: number;
    const timer = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const elapsed = timer.getElapsedTime();

      // Soft auto-rotation of whole constellation
      nodesGroup.rotation.y = elapsed * 0.05;
      nodesGroup.rotation.x = Math.sin(elapsed * 0.02) * 0.1;

      // Float individual nodes up and down procedurally
      nodeMeshes.forEach((mesh, index) => {
        mesh.position.y += Math.sin(elapsed * 1.5 + index) * 0.003;
      });

      // Raycast checks
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodeMeshes);

      if (intersects.length > 0) {
        const hoveredObject = intersects[0].object as THREE.Mesh;
        if (currentHoveredMesh !== hoveredObject) {
          // Reset previous hover
          if (currentHoveredMesh) {
            currentHoveredMesh.scale.set(1, 1, 1);
            (currentHoveredMesh.material as THREE.MeshPhongMaterial).emissiveIntensity = 0.15;
          }
          // Scale up and glow active node
          currentHoveredMesh = hoveredObject;
          currentHoveredMesh.scale.set(1.4, 1.4, 1.4);
          (currentHoveredMesh.material as THREE.MeshPhongMaterial).emissiveIntensity = 0.6;

          const paperIndex = hoveredObject.userData.paperIndex;
          setHoveredPaper(MOCK_PAPERS[paperIndex]);
        }
      } else {
        if (currentHoveredMesh) {
          currentHoveredMesh.scale.set(1, 1, 1);
          (currentHoveredMesh.material as THREE.MeshPhongMaterial).emissiveIntensity = 0.15;
          currentHoveredMesh = null;
          setHoveredPaper(null);
        }
      }

      renderer.render(scene, camera);
    };

    animate();

    // 9. Resize Handler
    const handleResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;

      camera.aspect = w / h;
      camera.updateProjectionMatrix();

      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    // Cleanup on unmount
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);

      if (containerRef.current && renderer.domElement) {
        // eslint-disable-next-line react-hooks/exhaustive-deps
        containerRef.current.removeChild(renderer.domElement);
      }

      // Dispose geometries & materials
      nodeGeometry.dispose();
      nodeMeshes.forEach(mesh => {
        (mesh.material as THREE.Material).dispose();
      });
      lineGeometry.dispose();
      lineMaterial.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden">
      {/* Floating Interactive Tooltip */}
      {hoveredPaper && (
        <div 
          className="fixed pointer-events-none z-50 bg-white/90 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-slate-200/60 shadow-xl space-y-1 transform -translate-x-1/2 -translate-y-full mt-[-15px] transition-all duration-150"
          style={{ left: mousePos.x, top: mousePos.y }}
        >
          <div className="flex items-center space-x-1.5 text-[10px] font-bold text-indigo-650 bg-indigo-50 px-2 py-0.5 rounded-full w-fit">
            <Sparkles className="w-3 h-3" />
            <span>{hoveredPaper.category}</span>
          </div>
          <h4 className="font-bold text-xs text-slate-800 leading-tight max-w-[200px]">
            {hoveredPaper.title}
          </h4>
          <span className="text-[10px] text-slate-400 block">
            Citations: {hoveredPaper.citations.toLocaleString()}
          </span>
        </div>
      )}

      {/* Floating HUD info */}
      <div className="absolute top-4 left-4 pointer-events-none">
        <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400 bg-white/40 backdrop-blur-sm border border-slate-200/40 px-2.5 py-1 rounded-full">
          Semantic Relation Engine
        </span>
      </div>
    </div>
  );
}
