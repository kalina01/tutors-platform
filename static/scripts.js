function pushQueryParams(newParams) {
    const params = new URLSearchParams(window.location.search);
    for (const [key, value] of Object.entries(newParams)) {
        if (value === undefined) {
            params.delete(key);
        } else {
            params.set(key, value);
        }
    }
    window.location.search = params.toString();
}
