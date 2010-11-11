function(doc) {
    if (doc.doctype == "node" && doc.meta.hash)
        emit(doc.meta.hash, doc);
}
