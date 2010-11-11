function(doc) {
    if (doc.doctype == "node" && doc.hash)
        emit(doc.hash, doc);
}
