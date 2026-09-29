// Safe DOM building: data is only ever inserted as text, never as HTML.
export function el(tag, attrs = {}, ...children) {
	const node = document.createElement(tag);
	for (const [key, value] of Object.entries(attrs)) {
		if (value === undefined || value === null || value === false) continue;
		if (key === 'class') node.className = value;
		else if (key === 'text') node.textContent = value;
		else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
		else if (key === 'style') Object.assign(node.style, value);
		else node.setAttribute(key, value === true ? '' : value);
	}
	for (const child of children.flat()) {
		if (child === null || child === undefined || child === false) continue;
		node.append(child instanceof Node ? child : document.createTextNode(String(child)));
	}
	return node;
}

export function clear(node) {
	while (node.firstChild) node.removeChild(node.firstChild);
	return node;
}
