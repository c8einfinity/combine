/**
 * Copyright (c) 2025 Code Infinity
 * Licensed under the MIT License
 * Author: Code Infinity
 *       : Jacques van Zuydam <jacques@codeinfinity.co.za>
 * Version: 1.0.0
 * Description: A simple profile image cropper with a circular overlay and blurred background for non-square images.
 * Dependencies: jQuery, Bootstrap (for modal)
 */

class ProfileCropper {
    /**
     * Constructor for ProfileCropper
     * @param fileInputId
     * @param cropContainer
     * @param modalId
     * @param options
     * @returns {ProfileCropper}
     * example options:
     * { size: 300, aspectRatio: 1, zoomStep: 0.1, enableDrag: true }
     */
    constructor(fileInputId, cropContainer, modalId, options = {}) {
        this.fileInput = document.getElementById(fileInputId);
        this.cropContainer = document.getElementById(cropContainer);
        this.modal = document.getElementById(modalId);
        this.originalImage = null;
        this.imageSrc = null;
        this.zoomAmount = 1;
        this.dimensions = { width: 0, height: 0 };
        this.offset = { x: 0, y: 0 };
        this.size = options.size || 300;
        if (options.enableDrag) {
            this.enableDrag();
        }
    }

    // attach event listener to file input
    init() {
        this.fileInput.addEventListener('change', (event) => this.handleFileSelect(event));
    }

    // handle file selection
    handleFileSelect(event) {
        // set the width and height of the crop container to the size
        this.cropContainer.style.width = `${this.size}px`;
        this.cropContainer.style.height = `${this.size}px`;
        this.cropContainer.style.position = 'relative';
        this.cropContainer.style.overflow = 'hidden';
        // add the image preview area
        const imagePreview = document.createElement('div');
        imagePreview.style.position = 'relative';
        imagePreview.style.width = '100%';
        imagePreview.style.height = '100%';
        this.cropContainer.innerHTML = '';
        this.cropContainer.appendChild(imagePreview);
        this.imagePreview = imagePreview;
        // add a circle overlay to the crop container
        const circleOverlay = document.createElement('div');
        circleOverlay.style.position = 'absolute';
        circleOverlay.style.top = '0';
        circleOverlay.style.left = '0';
        circleOverlay.style.width = '100%';
        circleOverlay.style.height = '100%';
        circleOverlay.style.borderRadius = '50%';
        circleOverlay.style.boxShadow = '0 0 0 2000px rgba(255, 255, 255, 0.5)';
        circleOverlay.style.pointerEvents = 'none';
        this.cropContainer.appendChild(circleOverlay);

        // append a second outlined circle to the crop container for the face placement
        const faceCircle = document.createElement('div');
        faceCircle.style.position = 'absolute';
        faceCircle.style.top = '40%';
        faceCircle.style.left = '50%';
        faceCircle.style.width = '130px';
        faceCircle.style.height = '150px';
        faceCircle.style.borderRadius = '50%';
        faceCircle.style.border = '2px dashed lightgray';
        faceCircle.style.transform = 'translate(-50%, -50%)';
        faceCircle.style.pointerEvents = 'none';
        this.cropContainer.appendChild(faceCircle);

        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => this.loadImage(e.target.result);
            reader.readAsDataURL(file);
        } else {
            alert('Please select a valid image file.');
        }
    }

    // Update loadImage to be async
    async loadImage(imageSrc) {
        this.dimensions = await this.getImageDimensions(imageSrc);
        let finalSrc = imageSrc;
        this.originalImage = imageSrc;
        // if the image is a png / webp, convert to jpg to avoid transparency issues
        if (imageSrc.startsWith('data:image/png') || imageSrc.startsWith('data:image/webp')) {
            finalSrc = this.flattenPngToJpg(imageSrc);
            this.originalImage = finalSrc;
        }

        if (this.dimensions.width !== this.dimensions.height) {
            const blurredData = await this.createBlurredBackground(imageSrc);
            finalSrc = blurredData.imageSrc;
            this.zoomAmount = 1;
        }
        this.imageSrc = finalSrc;
        this.setPreviewImage();
        $(`#${this.modal.id}`).modal('show');
    }

    // Add a helper for blurred background
    createBlurredBackground(imageSrc) {
        const dimensions = this.dimensions;
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            img.src = imageSrc;
            img.onload = function() {
                const size = this.size;
                canvas.width = size;
                canvas.height = size;
                ctx.clearRect(0, 0, size, size);
                ctx.filter = 'blur(25px)';
                ctx.drawImage(img, 0, 0, (size + 50), (size + 50));
                ctx.filter = 'none';
                const x = (size - dimensions.width) / 2;
                const y = (size - dimensions.height) / 2;
                ctx.drawImage(img, x, y, dimensions.width, dimensions.height);
                resolve( {imageSrc: canvas.toDataURL()} );
            }.bind(this)
            img.onerror = function() {
                resolve({imageSrc: imageSrc} );
            };
        });
    }

    setPreviewImage() {
        this.imagePreview.innerHTML = `<img src="${this.imageSrc}" style="max-width: 100%; display: block; margin: 0 auto;" alt="crop image" />`;
        const img = this.imagePreview.querySelector('img');
        img.addEventListener('dragstart', (e) => e.preventDefault());
    }

    /**
     * Set the zoom level directly.
     * @param zoomValue
     */
    setZoom(zoomValue) {
        if (this.imageSrc) {
            this.zoomAmount = zoomValue;
            if (this.zoomAmount < 0.1) this.zoomAmount = 0.1;
            this.drawZoomedImage();
        }
    }

    /**
     * Zoom in the image, manipulating the imageSrc.
     * To be bound to an external form control, e.g., a slider or button.
     */
    zoomIn(amount = 0.1) {
        if (this.imageSrc) {
            this.zoomAmount += amount;
            if (this.zoomAmount < 0.1) this.zoomAmount = 0.1;
            this.drawZoomedImage();
        }
    }

    /**
     * Zoom out the image, manipulating the imageSrc.
     * To be bound to an external form control, e.g., a slider or button.
     */
    async zoomOut(amount = 0.1) {
        if (this.imageSrc && this.originalImage) {
            this.zoomAmount -= amount;
            if (this.zoomAmount < 0.1) this.zoomAmount = 0.1;
            // redo the blurred background to eliminate white space
            this.drawZoomedImage();
        }
    }

    drawZoomedImage() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = this.originalImage;
        img.onload = async function () {
            // redraw the original image in a cropped canvas with the new zoom level
            const size = this.size;
            canvas.width = size;
            canvas.height = size;
            ctx.clearRect(0, 0, size, size);
            const newWidth = img.width * this.zoomAmount;
            const newHeight = img.height * this.zoomAmount;
            // use the offset to determine the position of the image
            let x = (size - newWidth) / 2 + this.offset.x;
            let y = (size - newHeight) / 2 + this.offset.y;
            // constrain x and y to prevent white space
            if (x > size - 10) x = size - 10; // allow some leeway
            if (x + newWidth < 10) x = 10 - newWidth;
            if (y > size - 10) y = size - 10;
            if (y + newHeight < 10) y = 10 - newHeight;
            // set dimensions for future use
            this.dimensions = { width: this.size, height: this.size };
            // blur the image to fill the background
            ctx.filter = 'blur(25px)';
            ctx.drawImage(img, 0, 0, size, size);
            ctx.filter = 'none';
            // draw the zoomed image
            ctx.drawImage(img, x, y, newWidth, newHeight);
            this.imageSrc = canvas.toDataURL();
            this.setPreviewImage();
        }.bind(this)
    }

    /**
     * Mouse click and drag to move the image within the crop area by setting the offset.
     * To be bound to mouse events on the crop container.
     */
    enableDrag() {
        let isDragging = false;
        let startX, startY;

        this.cropContainer.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX - this.offset.x;
            startY = e.clientY - this.offset.y;
        });

        this.cropContainer.addEventListener('mousemove', (e) => {
            if (isDragging) {
                this.offset.x = e.clientX - startX;
                this.offset.y = e.clientY - startY;
                this.drawZoomedImage();
            }
        });

        this.cropContainer.addEventListener('mouseup', () => {
            isDragging = false;
        });

        this.cropContainer.addEventListener('mouseleave', () => {
            isDragging = false;
        });
    }


    getCroppedImage() {
        return this.imageSrc;
    }

    /*
     * Get the image width and height
     */
    getImageDimensions(imageSrc) {
        return new Promise((resolve) => {
            const img = new Image();
            img.src = imageSrc;
            img.onload = function() {
                resolve({ width: this.width, height: this.height });
            };
            img.onerror = function() {
                resolve({ width: 0, height: 0 });
            };
        });
    }

    flattenPngToJpg(imageSrc) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = imageSrc;
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/jpeg', 1.0);
    }
}



