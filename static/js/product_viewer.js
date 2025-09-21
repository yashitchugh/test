renderer.domElement.addEventListener('click', function(event) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);

    if (model) {
        // Change from model.children to all descendants:
        const meshes = [];
        model.traverse(child => {
            if (child.isMesh) meshes.push(child);
        });
        const intersects = raycaster.intersectObjects(meshes);
        if (intersects.length > 0) {
            selectedMesh = intersects[0].object;
            document.getElementById('info').textContent = "Selected part: " + (selectedMesh.name || "unnamed mesh");
        }
    }
});

