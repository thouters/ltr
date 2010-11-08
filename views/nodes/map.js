function(doc) {
    if (doc.doctype == "node") 
        emit(doc.path, doc._id);
}
