FROM nginx:alpine
COPY src/ /usr/share/nginx/html
COPY index.html /usr/share/nginx/html/index.html

CMD ["nginx", "-g", "daemon off;"]